package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"time"

	coreumapp "github.com/CoreumFoundation/coreum/app"
	coreumconfig "github.com/CoreumFoundation/coreum/pkg/config"
	servertypes "github.com/cosmos/cosmos-sdk/server/types"
	abci "github.com/tendermint/tendermint/abci/types"
	"github.com/tendermint/tendermint/crypto/merkle"
	tmjson "github.com/tendermint/tendermint/libs/json"
	tmlog "github.com/tendermint/tendermint/libs/log"
	mmock "github.com/tendermint/tendermint/mempool/mock"
	"github.com/tendermint/tendermint/proxy"
	coretypes "github.com/tendermint/tendermint/rpc/core/types"
	sm "github.com/tendermint/tendermint/state"
	tmtypes "github.com/tendermint/tendermint/types"
	dbm "github.com/tendermint/tm-db"
)

type opts map[string]interface{}
var _ servertypes.AppOptions = opts{}
func (o opts) Get(k string) interface{} { return o[k] }

type blockEnvelope struct { Result coretypes.ResultBlock `json:"result"` }
func hx(b []byte) string { return fmt.Sprintf("%X", b) }

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
	computed := b.Hash()
	if !bytes.Equal(computed, env.Result.BlockID.Hash) {
		panic(fmt.Sprintf("block hash mismatch H=%d computed=%s reported=%s", height, hx(computed), hx(env.Result.BlockID.Hash)))
	}
	return env.Result
}

func openDB(name, dir string) dbm.DB {
	db, err := dbm.NewGoLevelDB(name, dir)
	if err != nil { panic(err) }
	return db
}

func main() {
	configureMainnet()
	if len(os.Args) != 7 {
		fmt.Fprintln(os.Stderr, "usage: native_chunk_v1 <genesis.json> <block_dir> <db_dir> <home_dir> <start_height> <end_height>")
		os.Exit(2)
	}
	startHeight, _ := strconv.ParseInt(os.Args[5], 10, 64)
	endHeight, _ := strconv.ParseInt(os.Args[6], 10, 64)
	if startHeight < 1 || endHeight < startHeight { panic("invalid range") }

	genRaw, err := os.ReadFile(os.Args[1]); if err != nil { panic(err) }
	gen, err := tmtypes.GenesisDocFromJSON(genRaw); if err != nil { panic(err) }
	if gen.ChainID != "coreum-mainnet-1" { panic("genesis chain-id mismatch") }

	dbDir := os.Args[3]
	home := os.Args[4]
	if err := os.MkdirAll(dbDir, 0755); err != nil { panic(err) }
	if err := os.MkdirAll(home, 0755); err != nil { panic(err) }

	appDB := openDB("application", dbDir); defer appDB.Close()
	stateDB := openDB("state", dbDir); defer stateDB.Close()
	encoding := coreumconfig.NewEncodingConfig(coreumapp.ModuleBasics)

	isGenesis := startHeight == 1
	app := coreumapp.New(
		tmlog.NewNopLogger(), appDB, nil, true,
		map[int64]bool{}, home, 0, encoding, opts{},
	)

	stateStore := sm.NewStore(stateDB, sm.StoreOptions{DiscardABCIResponses: false})
	var state sm.State

	cc := proxy.NewLocalClientCreator(app)
	proxyApp := proxy.NewAppConns(cc)
	if err := proxyApp.Start(); err != nil { panic(err) }
	defer proxyApp.Stop()

	if isGenesis {
		state, err = sm.MakeGenesisState(gen); if err != nil { panic(err) }
		genVals := make([]*tmtypes.Validator, len(gen.Validators))
		for i, val := range gen.Validators { genVals[i] = tmtypes.NewValidator(val.PubKey, val.Power) }
		valSet := tmtypes.NewValidatorSet(genVals)
		initResp, err := proxyApp.Consensus().InitChainSync(abci.RequestInitChain{
			Time: gen.GenesisTime, ChainId: gen.ChainID, InitialHeight: gen.InitialHeight,
			ConsensusParams: tmtypes.TM2PB.ConsensusParams(gen.ConsensusParams),
			Validators: tmtypes.TM2PB.ValidatorUpdates(valSet), AppStateBytes: gen.AppState,
		})
		if err != nil { panic(err) }
		if len(initResp.AppHash) > 0 { state.AppHash = initResp.AppHash }
		if len(initResp.Validators) > 0 {
			vals, err := tmtypes.PB2TM.ValidatorUpdates(initResp.Validators); if err != nil { panic(err) }
			state.Validators = tmtypes.NewValidatorSet(vals)
			state.NextValidators = tmtypes.NewValidatorSet(vals).CopyIncrementProposerPriority(1)
		} else if len(gen.Validators) == 0 { panic("validator set empty after InitChain") }
		if initResp.ConsensusParams != nil {
			state.ConsensusParams = tmtypes.UpdateConsensusParams(state.ConsensusParams, initResp.ConsensusParams)
			state.Version.Consensus.App = state.ConsensusParams.Version.AppVersion
		}
		state.LastResultsHash = merkle.HashFromByteSlices(nil)
		if err := stateStore.Save(state); err != nil { panic(err) }
	} else {
		state, err = stateStore.Load(); if err != nil { panic(err) }
		if state.LastBlockHeight != startHeight-1 {
			panic(fmt.Sprintf("resume height mismatch state=%d start=%d", state.LastBlockHeight, startHeight))
		}
		if app.LastBlockHeight() != startHeight-1 {
			panic(fmt.Sprintf("application height mismatch app=%d start=%d", app.LastBlockHeight(), startHeight))
		}
	}

	first := readBlock(os.Args[2], startHeight)
	if !bytes.Equal(first.Block.Header.ValidatorsHash, state.Validators.Hash()) {
		panic(fmt.Sprintf("validator hash mismatch at start H=%d state=%s header=%s", startHeight, hx(state.Validators.Hash()), hx(first.Block.Header.ValidatorsHash)))
	}

	blockExec := sm.NewBlockExecutor(stateStore, tmlog.NewNopLogger(), proxyApp.Consensus(), mmock.Mempool{}, sm.EmptyEvidencePool{})
	var txTotal int
	var evidenceTotal int
	started := time.Now()
	for h := startHeight; h <= endHeight; h++ {
		cur := readBlock(os.Args[2], h)
		next := readBlock(os.Args[2], h+1)
		newState, _, err := blockExec.ApplyBlock(state, cur.BlockID, cur.Block)
		if err != nil { panic(fmt.Errorf("ApplyBlock H=%d: %w", h, err)) }
		if newState.LastBlockHeight != h { panic(fmt.Sprintf("state height mismatch H=%d got=%d", h, newState.LastBlockHeight)) }
		if !bytes.Equal(newState.AppHash, next.Block.Header.AppHash) {
			panic(fmt.Sprintf("AppHash offset mismatch H=%d local=%s next_header=%s", h, hx(newState.AppHash), hx(next.Block.Header.AppHash)))
		}
		resp, err := stateStore.LoadABCIResponses(h); if err != nil { panic(err) }
		if resp == nil || resp.BeginBlock == nil || resp.EndBlock == nil { panic(fmt.Sprintf("incomplete ABCI response H=%d", h)) }
		if len(resp.DeliverTxs) != len(cur.Block.Data.Txs) { panic(fmt.Sprintf("DeliverTx count mismatch H=%d", h)) }
		txTotal += len(cur.Block.Data.Txs)
		evidenceTotal += len(cur.Block.Evidence.Evidence)
		state = newState
	}

	elapsed := time.Since(started).Seconds()
	out := map[string]interface{}{
		"chain_id": gen.ChainID,
		"start_height": startHeight,
		"end_height": endHeight,
		"blocks_applied": endHeight-startHeight+1,
		"tx_count_total": txTotal,
		"evidence_count_total": evidenceTotal,
		"elapsed_seconds": elapsed,
		"blocks_per_second": float64(endHeight-startHeight+1) / elapsed,
		"final_app_hash": hx(state.AppHash),
		"all_app_hash_offsets_pass": true,
		"persistent_leveldb": true,
		"resume_capable": true,
		"canonical_last_commit_verified_by_block_executor": true,
		"canonical_evidence_forwarded_to_abci": true,
		"block_results_consumed_from_rpc": false,
		"census_executed": false,
		"market_outcomes_opened": false,
	}
	raw, _ := json.MarshalIndent(out, "", "  ")
	fmt.Println(string(raw))
}
