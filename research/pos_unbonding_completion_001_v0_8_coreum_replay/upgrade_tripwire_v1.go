package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"

	coreumapp "github.com/CoreumFoundation/coreum/app"
	coreumconfig "github.com/CoreumFoundation/coreum/pkg/config"
	servertypes "github.com/cosmos/cosmos-sdk/server/types"
	tmjson "github.com/tendermint/tendermint/libs/json"
	tmlog "github.com/tendermint/tendermint/libs/log"
	mmock "github.com/tendermint/tendermint/mempool/mock"
	"github.com/tendermint/tendermint/proxy"
	coretypes "github.com/tendermint/tendermint/rpc/core/types"
	sm "github.com/tendermint/tendermint/state"
	dbm "github.com/tendermint/tm-db"
)

type opts map[string]interface{}
var _ servertypes.AppOptions = opts{}
func (o opts) Get(k string) interface{} { return o[k] }

type blockEnvelope struct { Result coretypes.ResultBlock `json:"result"` }
type upgradeInfo struct {
	Name string `json:"name"`
	Height int64 `json:"height"`
	Info string `json:"info,omitempty"`
}

func configureMainnet() {
	for _, network := range coreumconfig.Networks() {
		if string(network.ChainID()) == "coreum-mainnet-1" {
			network.SetSDKConfig()
			coreumapp.ChosenNetwork = network
			return
		}
	}
	panic("coreum-mainnet-1 network config not found")
}

func openDB(name, dir string) dbm.DB {
	db, err := dbm.NewGoLevelDB(name, dir)
	if err != nil { panic(err) }
	return db
}

func readBlock(dir string, h int64) coretypes.ResultBlock {
	raw, err := os.ReadFile(filepath.Join(dir, fmt.Sprintf("block_%d.json", h)))
	if err != nil { panic(err) }
	var env blockEnvelope
	if err := tmjson.Unmarshal(raw, &env); err != nil { panic(err) }
	if env.Result.Block == nil || env.Result.Block.Header.Height != h { panic("block identity mismatch") }
	if env.Result.Block.Header.ChainID != "coreum-mainnet-1" { panic("chain-id mismatch") }
	if !bytes.Equal(env.Result.Block.Hash(), env.Result.BlockID.Hash) { panic("block hash mismatch") }
	return env.Result
}

func main() {
	configureMainnet()
	if len(os.Args) != 7 {
		fmt.Fprintln(os.Stderr, "usage: upgrade_tripwire_v1 <block_dir> <db_dir> <home_dir> <upgrade_height> <upgrade_name> <expected_pre_height>")
		os.Exit(2)
	}
	blockDir, dbDir, home := os.Args[1], os.Args[2], os.Args[3]
	upgradeHeight, _ := strconv.ParseInt(os.Args[4], 10, 64)
	upgradeName := os.Args[5]
	expectedPre, _ := strconv.ParseInt(os.Args[6], 10, 64)
	if upgradeHeight != expectedPre+1 { panic("upgrade/pre-height mismatch") }

	appDB := openDB("application", dbDir); defer appDB.Close()
	stateDB := openDB("state", dbDir); defer stateDB.Close()
	encoding := coreumconfig.NewEncodingConfig(coreumapp.ModuleBasics)
	app := coreumapp.New(tmlog.NewNopLogger(), appDB, nil, true, map[int64]bool{}, home, 0, encoding, opts{})
	stateStore := sm.NewStore(stateDB, sm.StoreOptions{DiscardABCIResponses:false})
	state, err := stateStore.Load(); if err != nil { panic(err) }
	if state.LastBlockHeight != expectedPre { panic(fmt.Sprintf("state pre-height=%d want=%d",state.LastBlockHeight,expectedPre)) }
	if app.LastBlockHeight() != expectedPre { panic(fmt.Sprintf("app pre-height=%d want=%d",app.LastBlockHeight(),expectedPre)) }

	cc := proxy.NewLocalClientCreator(app)
	proxyApp := proxy.NewAppConns(cc)
	if err := proxyApp.Start(); err != nil { panic(err) }
	defer proxyApp.Stop()
	blockExec := sm.NewBlockExecutor(stateStore, tmlog.NewNopLogger(), proxyApp.Consensus(), mmock.Mempool{}, sm.EmptyEvidencePool{})
	cur := readBlock(blockDir, upgradeHeight)

	var recovered interface{}
	func() {
		defer func(){ recovered = recover() }()
		_, _, _ = blockExec.ApplyBlock(state, cur.BlockID, cur.Block)
	}()
	if recovered == nil { panic("old binary unexpectedly executed upgrade block without upgrade panic") }

	infoPath := filepath.Join(home,"data","upgrade-info.json")
	raw, err := os.ReadFile(infoPath); if err != nil { panic(fmt.Errorf("upgrade info missing after panic: %w",err)) }
	var info upgradeInfo
	if err := json.Unmarshal(raw,&info); err != nil { panic(err) }
	if info.Name != upgradeName || info.Height != upgradeHeight {
		panic(fmt.Sprintf("upgrade info mismatch got=%s@%d want=%s@%d",info.Name,info.Height,upgradeName,upgradeHeight))
	}

	afterState, err := stateStore.Load(); if err != nil { panic(err) }
	if afterState.LastBlockHeight != expectedPre { panic("consensus state advanced despite upgrade panic") }
	if app.LastBlockHeight() != expectedPre { panic("application state advanced despite upgrade panic") }

	out:=map[string]interface{}{
		"chain_id":"coreum-mainnet-1",
		"upgrade_name":upgradeName,
		"upgrade_height":upgradeHeight,
		"pre_height":expectedPre,
		"upgrade_info_path":infoPath,
		"upgrade_info":info,
		"old_binary_panicked":true,
		"consensus_state_not_advanced":true,
		"application_state_not_advanced":true,
		"ready_for_successor_binary":true,
		"census_executed":false,
		"market_outcomes_opened":false,
	}
	b,_:=json.MarshalIndent(out,"","  ")
	fmt.Println(string(b))
}
