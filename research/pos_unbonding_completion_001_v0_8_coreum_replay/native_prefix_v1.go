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

type blockEnvelope struct {
	Result coretypes.ResultBlock
}

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
	if err != nil {
		panic(err)
	}
	var env blockEnvelope
	if err := tmjson.Unmarshal(raw, &env); err != nil {
		panic(fmt.Errorf("decode %s: %w", path, err))
	}
	if env.Result.Block == nil {
		panic(fmt.Sprintf("nil block at H=%d", height))
	}
	if env.Result.Block.Header.Height != height {
		panic(fmt.Sprintf("height mismatch file H=%d header=%d", height, env.Result.Block.Header.Height))
	}
	return env.Result
}

func main() {
	configureMainnet()
	if len(os.Args) != 4 {
		fmt.Fprintln(os.Stderr, "usage: native_prefix_v1 <genesis.json> <block_dir> <end_height>")
		os.Exit(2)
	}
	endHeight, err := strconv.ParseInt(os.Args[3], 10, 64)
	if err != nil || endHeight < 1 {
		panic("invalid end_height")
	}

	genRaw, err := os.ReadFile(os.Args[1])
	if err != nil {
		panic(err)
	}
	gen, err := tmtypes.GenesisDocFromJSON(genRaw)
	if err != nil {
		panic(err)
	}
	if gen.ChainID != "coreum-mainnet-1" {
		panic("genesis chain-id mismatch")
	}

	home, err := os.MkdirTemp("", "coreum-v1-native-prefix-")
	if err != nil {
		panic(err)
	}
	defer os.RemoveAll(home)

	encoding := coreumconfig.NewEncodingConfig(coreumapp.ModuleBasics)
	app := coreumapp.New(
		tmlog.NewNopLogger(),
		dbm.NewMemDB(),
		nil,
		true,
		map[int64]bool{},
		home,
		0,
		encoding,
		opts{},
	)

	state, err := sm.MakeGenesisState(gen)
	if err != nil {
		panic(err)
	}
	stateStore := sm.NewStore(dbm.NewMemDB(), sm.StoreOptions{DiscardABCIResponses: false})

	cc := proxy.NewLocalClientCreator(app)
	proxyApp := proxy.NewAppConns(cc)
	if err := proxyApp.Start(); err != nil {
		panic(err)
	}
	defer proxyApp.Stop()

	genVals := make([]*tmtypes.Validator, len(gen.Validators))
	for i, val := range gen.Validators {
		genVals[i] = tmtypes.NewValidator(val.PubKey, val.Power)
	}
	valSet := tmtypes.NewValidatorSet(genVals)
	initResp, err := proxyApp.Consensus().InitChainSync(abci.RequestInitChain{
		Time:            gen.GenesisTime,
		ChainId:         gen.ChainID,
		InitialHeight:   gen.InitialHeight,
		ConsensusParams: tmtypes.TM2PB.ConsensusParams(gen.ConsensusParams),
		Validators:      tmtypes.TM2PB.ValidatorUpdates(valSet),
		AppStateBytes:   gen.AppState,
	})
	if err != nil {
		panic(err)
	}
	if len(initResp.AppHash) > 0 {
		state.AppHash = initResp.AppHash
	}
	if len(initResp.Validators) > 0 {
		vals, err := tmtypes.PB2TM.ValidatorUpdates(initResp.Validators)
		if err != nil {
			panic(err)
		}
		state.Validators = tmtypes.NewValidatorSet(vals)
		state.NextValidators = tmtypes.NewValidatorSet(vals).CopyIncrementProposerPriority(1)
	} else if len(gen.Validators) == 0 {
		panic("validator set empty after InitChain")
	}
	if initResp.ConsensusParams != nil {
		state.ConsensusParams = tmtypes.UpdateConsensusParams(state.ConsensusParams, initResp.ConsensusParams)
		state.Version.Consensus.App = state.ConsensusParams.Version.AppVersion
	}
	state.LastResultsHash = merkle.HashFromByteSlices(nil)
	if err := stateStore.Save(state); err != nil {
		panic(err)
	}

	first := readBlock(os.Args[2], 1)
	if !bytes.Equal(first.Block.Header.ValidatorsHash, state.Validators.Hash()) {
		panic(fmt.Sprintf("post-InitChain validator hash mismatch got=%s want=%s", hx(state.Validators.Hash()), hx(first.Block.Header.ValidatorsHash)))
	}

	blockExec := sm.NewBlockExecutor(
		stateStore,
		tmlog.NewNopLogger(),
		proxyApp.Consensus(),
		mmock.Mempool{},
		sm.EmptyEvidencePool{},
	)

	receipts := make([]map[string]interface{}, 0, endHeight)
	for h := int64(1); h <= endHeight; h++ {
		cur := readBlock(os.Args[2], h)
		next := readBlock(os.Args[2], h+1)
		if len(cur.Block.Evidence.Evidence) != 0 {
			panic(fmt.Sprintf("H=%d contains evidence; bounded pilot refuses unverified evidence pool shortcut", h))
		}
		newState, retainHeight, err := blockExec.ApplyBlock(state, cur.BlockID, cur.Block)
		if err != nil {
			panic(fmt.Errorf("ApplyBlock H=%d: %w", h, err))
		}
		if newState.LastBlockHeight != h {
			panic(fmt.Sprintf("state height mismatch H=%d got=%d", h, newState.LastBlockHeight))
		}
		appHashPass := bytes.Equal(newState.AppHash, next.Block.Header.AppHash)
		if !appHashPass {
			panic(fmt.Sprintf("AppHash offset mismatch H=%d local=%s next_header=%s", h, hx(newState.AppHash), hx(next.Block.Header.AppHash)))
		}
		resp, err := stateStore.LoadABCIResponses(h)
		if err != nil {
			panic(fmt.Errorf("ABCI response load H=%d: %w", h, err))
		}
		if resp == nil || resp.BeginBlock == nil || resp.EndBlock == nil {
			panic(fmt.Sprintf("incomplete local ABCI response H=%d", h))
		}
		if len(resp.DeliverTxs) != len(cur.Block.Data.Txs) {
			panic(fmt.Sprintf("DeliverTx response count mismatch H=%d got=%d want=%d", h, len(resp.DeliverTxs), len(cur.Block.Data.Txs)))
		}
		receipts = append(receipts, map[string]interface{}{
			"height": h,
			"block_hash": hx(cur.BlockID.Hash),
			"block_time": cur.Block.Header.Time.UTC().Format("2006-01-02T15:04:05.999999999Z"),
			"tx_count": len(cur.Block.Data.Txs),
			"local_app_hash_after": hx(newState.AppHash),
			"next_header_app_hash": hx(next.Block.Header.AppHash),
			"app_hash_offset_pass": true,
			"abci_responses_persisted": true,
			"retain_height": retainHeight,
		})
		state = newState
	}

	out := map[string]interface{}{
		"chain_id": gen.ChainID,
		"initial_height": gen.InitialHeight,
		"end_height": endHeight,
		"blocks_applied": len(receipts),
		"native_tendermint_block_executor": true,
		"empty_evidence_shortcut_used_only_after_zero_evidence_assertion": true,
		"all_app_hash_offsets_pass": true,
		"block_results_consumed_from_rpc": false,
		"census_executed": false,
		"market_outcomes_opened": false,
		"receipts": receipts,
	}
	raw, _ := json.MarshalIndent(out, "", "  ")
	fmt.Println(string(raw))
}
