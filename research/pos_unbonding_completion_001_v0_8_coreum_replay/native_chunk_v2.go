package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"time"

	coreumapp "github.com/CoreumFoundation/coreum/v2/app"
	coreumconfig "github.com/CoreumFoundation/coreum/v2/pkg/config"
	coreumconstant "github.com/CoreumFoundation/coreum/v2/pkg/config/constant"
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
func hx(b []byte) string { return fmt.Sprintf("%X", b) }

func configureMainnet() {
	network, err := coreumconfig.NetworkConfigByChainID(coreumconstant.ChainIDMain)
	if err != nil { panic(err) }
	network.SetSDKConfig()
	coreumapp.ChosenNetwork = network
	if string(network.ChainID()) != "coreum-mainnet-1" { panic("mainnet chain-id mismatch") }
}

func openDB(name, dir string) dbm.DB {
	db, err := dbm.NewGoLevelDB(name, dir)
	if err != nil { panic(err) }
	return db
}

func readBlock(dir string, height int64) coretypes.ResultBlock {
	path := filepath.Join(dir, fmt.Sprintf("block_%d.json", height))
	raw, err := os.ReadFile(path)
	if err != nil { panic(err) }
	var env blockEnvelope
	if err := tmjson.Unmarshal(raw, &env); err != nil { panic(fmt.Errorf("decode %s: %w", path, err)) }
	if env.Result.Block == nil { panic(fmt.Sprintf("nil block at H=%d", height)) }
	b := env.Result.Block
	if b.Header.Height != height { panic(fmt.Sprintf("height mismatch file H=%d header=%d", height, b.Header.Height)) }
	if b.Header.ChainID != "coreum-mainnet-1" { panic(fmt.Sprintf("chain-id mismatch H=%d", height)) }
	if !bytes.Equal(b.Hash(), env.Result.BlockID.Hash) {
		panic(fmt.Sprintf("block hash mismatch H=%d computed=%s reported=%s", height, hx(b.Hash()), hx(env.Result.BlockID.Hash)))
	}
	return env.Result
}

func main() {
	configureMainnet()
	if len(os.Args) != 6 {
		fmt.Fprintln(os.Stderr, "usage: native_chunk_v2 <block_dir> <db_dir> <home_dir> <start_height> <end_height>")
		os.Exit(2)
	}
	startHeight, err := strconv.ParseInt(os.Args[4], 10, 64)
	if err != nil { panic(err) }
	endHeight, err := strconv.ParseInt(os.Args[5], 10, 64)
	if err != nil || startHeight < 1 || endHeight < startHeight { panic("invalid range") }

	dbDir, home := os.Args[2], os.Args[3]
	appDB := openDB("application", dbDir); defer appDB.Close()
	stateDB := openDB("state", dbDir); defer stateDB.Close()
	encoding := coreumconfig.NewEncodingConfig(coreumapp.ModuleBasics)

	app := coreumapp.New(
		tmlog.NewNopLogger(), appDB, nil, true,
		map[int64]bool{}, home, 0, encoding, opts{},
	)
	stateStore := sm.NewStore(stateDB, sm.StoreOptions{DiscardABCIResponses:false})
	state, err := stateStore.Load(); if err != nil { panic(err) }
	if state.LastBlockHeight != startHeight-1 {
		panic(fmt.Sprintf("resume height mismatch state=%d start=%d", state.LastBlockHeight, startHeight))
	}
	if app.LastBlockHeight() != startHeight-1 {
		panic(fmt.Sprintf("application height mismatch app=%d start=%d", app.LastBlockHeight(), startHeight))
	}

	first := readBlock(os.Args[1], startHeight)
	if !bytes.Equal(first.Block.Header.ValidatorsHash, state.Validators.Hash()) {
		panic(fmt.Sprintf("validator hash mismatch at start H=%d", startHeight))
	}

	cc := proxy.NewLocalClientCreator(app)
	proxyApp := proxy.NewAppConns(cc)
	if err := proxyApp.Start(); err != nil { panic(err) }
	defer proxyApp.Stop()
	blockExec := sm.NewBlockExecutor(stateStore, tmlog.NewNopLogger(), proxyApp.Consensus(), mmock.Mempool{}, sm.EmptyEvidencePool{})

	var txTotal, evidenceTotal int
	started := time.Now()
	for h := startHeight; h <= endHeight; h++ {
		cur := readBlock(os.Args[1], h)
		next := readBlock(os.Args[1], h+1)
		newState, _, err := blockExec.ApplyBlock(state, cur.BlockID, cur.Block)
		if err != nil { panic(fmt.Errorf("ApplyBlock H=%d: %w", h, err)) }
		if newState.LastBlockHeight != h { panic(fmt.Sprintf("state height mismatch H=%d got=%d",h,newState.LastBlockHeight)) }
		if !bytes.Equal(newState.AppHash, next.Block.Header.AppHash) {
			panic(fmt.Sprintf("AppHash offset mismatch H=%d local=%s next=%s",h,hx(newState.AppHash),hx(next.Block.Header.AppHash)))
		}
		resp, err := stateStore.LoadABCIResponses(h); if err != nil { panic(err) }
		if resp == nil || resp.BeginBlock == nil || resp.EndBlock == nil { panic(fmt.Sprintf("incomplete ABCI response H=%d",h)) }
		if len(resp.DeliverTxs) != len(cur.Block.Data.Txs) { panic(fmt.Sprintf("DeliverTx count mismatch H=%d",h)) }
		txTotal += len(cur.Block.Data.Txs)
		evidenceTotal += len(cur.Block.Evidence.Evidence)
		state = newState
	}

	elapsed:=time.Since(started).Seconds()
	out:=map[string]interface{}{
		"chain_id":"coreum-mainnet-1",
		"application_version":"v2.0.2",
		"start_height":startHeight,
		"end_height":endHeight,
		"blocks_applied":endHeight-startHeight+1,
		"tx_count_total":txTotal,
		"evidence_count_total":evidenceTotal,
		"final_app_hash":hx(state.AppHash),
		"all_app_hash_offsets_pass":true,
		"persistent_leveldb":true,
		"resume_capable":true,
		"canonical_last_commit_verified_by_block_executor":true,
		"canonical_evidence_forwarded_to_abci":true,
		"elapsed_seconds":elapsed,
		"blocks_per_second":float64(endHeight-startHeight+1)/elapsed,
		"block_results_consumed_from_rpc":false,
		"census_executed":false,
		"market_outcomes_opened":false,
	}
	raw,_:=json.MarshalIndent(out,"","  ")
	fmt.Println(string(raw))
}
