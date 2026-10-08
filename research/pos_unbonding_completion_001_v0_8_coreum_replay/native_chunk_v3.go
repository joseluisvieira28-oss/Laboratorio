package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"time"

	coreumapp "github.com/CoreumFoundation/coreum/v3/app"
	coreumconfig "github.com/CoreumFoundation/coreum/v3/pkg/config"
	coreumconstant "github.com/CoreumFoundation/coreum/v3/pkg/config/constant"
	abci "github.com/cometbft/cometbft/abci/types"
	dbm "github.com/cometbft/cometbft-db"
	cmtjson "github.com/cometbft/cometbft/libs/json"
	cmtlog "github.com/cometbft/cometbft/libs/log"
	"github.com/cometbft/cometbft/mempool"
	"github.com/cometbft/cometbft/proxy"
	coretypes "github.com/cometbft/cometbft/rpc/core/types"
	sm "github.com/cometbft/cometbft/state"
	cmttypes "github.com/cometbft/cometbft/types"
	"github.com/cosmos/cosmos-sdk/client/flags"
	"github.com/cosmos/cosmos-sdk/server"
	servertypes "github.com/cosmos/cosmos-sdk/server/types"
)

type opts map[string]interface{}
var _ servertypes.AppOptions = opts{}
func (o opts) Get(k string) interface{} { return o[k] }

type emptyMempool struct{}
func (emptyMempool) CheckTx(cmttypes.Tx, func(*abci.Response), mempool.TxInfo) error { return nil }
func (emptyMempool) RemoveTxByKey(cmttypes.TxKey) error { return nil }
func (emptyMempool) ReapMaxBytesMaxGas(int64,int64) cmttypes.Txs { return nil }
func (emptyMempool) ReapMaxTxs(int) cmttypes.Txs { return nil }
func (emptyMempool) Lock() {}
func (emptyMempool) Unlock() {}
func (emptyMempool) Update(int64,cmttypes.Txs,[]*abci.ResponseDeliverTx,mempool.PreCheckFunc,mempool.PostCheckFunc) error { return nil }
func (emptyMempool) FlushAppConn() error { return nil }
func (emptyMempool) Flush() {}
func (emptyMempool) TxsAvailable() <-chan struct{} { return nil }
func (emptyMempool) EnableTxsAvailable() {}
func (emptyMempool) Size() int { return 0 }
func (emptyMempool) SizeBytes() int64 { return 0 }

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
	if err := cmtjson.Unmarshal(raw, &env); err != nil { panic(fmt.Errorf("decode %s: %w", path, err)) }
	if env.Result.Block == nil { panic(fmt.Sprintf("nil block at H=%d",height)) }
	b:=env.Result.Block
	if b.Header.Height != height { panic("height mismatch") }
	if b.Header.ChainID != "coreum-mainnet-1" { panic("chain-id mismatch") }
	if !bytes.Equal(b.Hash(),env.Result.BlockID.Hash) {
		panic(fmt.Sprintf("block hash mismatch H=%d computed=%s reported=%s",height,hx(b.Hash()),hx(env.Result.BlockID.Hash)))
	}
	return env.Result
}

func main() {
	configureMainnet()
	if len(os.Args) != 6 {
		fmt.Fprintln(os.Stderr,"usage: native_chunk_v3 <block_dir> <db_dir> <home_dir> <start_height> <end_height>")
		os.Exit(2)
	}
	startHeight,err:=strconv.ParseInt(os.Args[4],10,64); if err!=nil { panic(err) }
	endHeight,err:=strconv.ParseInt(os.Args[5],10,64); if err!=nil || startHeight<1 || endHeight<startHeight { panic("invalid range") }
	dbDir,home:=os.Args[2],os.Args[3]

	appDB:=openDB("application",dbDir); defer appDB.Close()
	stateDB:=openDB("state",dbDir); defer stateDB.Close()
	appOpts:=opts{
		flags.FlagHome:home,
		server.FlagInvCheckPeriod:uint(0),
		server.FlagUnsafeSkipUpgrades:[]int{},
		"telemetry.enabled":false,
	}
	app:=coreumapp.New(cmtlog.NewNopLogger(),appDB,nil,true,appOpts)
	stateStore:=sm.NewStore(stateDB,sm.StoreOptions{DiscardABCIResponses:false})
	state,err:=stateStore.Load(); if err!=nil { panic(err) }
	if state.LastBlockHeight!=startHeight-1 { panic(fmt.Sprintf("resume height mismatch state=%d start=%d",state.LastBlockHeight,startHeight)) }
	if app.LastBlockHeight()!=startHeight-1 { panic(fmt.Sprintf("application height mismatch app=%d start=%d",app.LastBlockHeight(),startHeight)) }

	first:=readBlock(os.Args[1],startHeight)
	if !bytes.Equal(first.Block.Header.ValidatorsHash,state.Validators.Hash()) { panic("validator hash mismatch at start") }

	cc:=proxy.NewLocalClientCreator(app)
	proxyApp:=proxy.NewAppConns(cc,proxy.NopMetrics())
	if err:=proxyApp.Start(); err!=nil { panic(err) }
	defer proxyApp.Stop()
	blockExec:=sm.NewBlockExecutor(stateStore,cmtlog.NewNopLogger(),proxyApp.Consensus(),emptyMempool{},sm.EmptyEvidencePool{})

	var txTotal,evidenceTotal int
	started:=time.Now()
	for h:=startHeight; h<=endHeight; h++ {
		cur:=readBlock(os.Args[1],h)
		next:=readBlock(os.Args[1],h+1)
		newState,_,err:=blockExec.ApplyBlock(state,cur.BlockID,cur.Block)
		if err!=nil { panic(fmt.Errorf("ApplyBlock H=%d: %w",h,err)) }
		if newState.LastBlockHeight!=h { panic("state height mismatch") }
		if !bytes.Equal(newState.AppHash,next.Block.Header.AppHash) {
			panic(fmt.Sprintf("AppHash offset mismatch H=%d local=%s next=%s",h,hx(newState.AppHash),hx(next.Block.Header.AppHash)))
		}
		resp,err:=stateStore.LoadABCIResponses(h); if err!=nil { panic(err) }
		if resp==nil || resp.BeginBlock==nil || resp.EndBlock==nil { panic(fmt.Sprintf("incomplete ABCI response H=%d",h)) }
		if len(resp.DeliverTxs)!=len(cur.Block.Data.Txs) { panic(fmt.Sprintf("DeliverTx count mismatch H=%d",h)) }
		txTotal+=len(cur.Block.Data.Txs)
		evidenceTotal+=len(cur.Block.Evidence.Evidence)
		state=newState
	}
	elapsed:=time.Since(started).Seconds()
	out:=map[string]interface{}{
		"chain_id":"coreum-mainnet-1",
		"application_version":"v3.0.3",
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
