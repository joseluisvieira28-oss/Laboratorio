package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	coreumapp "github.com/CoreumFoundation/coreum/app"
	coreumconfig "github.com/CoreumFoundation/coreum/pkg/config"
	servertypes "github.com/cosmos/cosmos-sdk/server/types"
	abci "github.com/tendermint/tendermint/abci/types"
	tmjson "github.com/tendermint/tendermint/libs/json"
	tmlog "github.com/tendermint/tendermint/libs/log"
	tmtypes "github.com/tendermint/tendermint/types"
	dbm "github.com/tendermint/tm-db"
)

type opts map[string]interface{}

var _ servertypes.AppOptions = opts{}

func (o opts) Get(k string) interface{} { return o[k] }

type blockEnvelope struct {
	Result struct {
		BlockID tmtypes.BlockID `json:"block_id"`
		Block   *tmtypes.Block  `json:"block"`
	} `json:"result"`
}

type receipt struct {
	ChainID                   string `json:"chain_id"`
	InitialHeight             int64  `json:"initial_height"`
	InitChainValidatorUpdates int    `json:"init_chain_validator_updates"`
	InitChainValidatorsHash   string `json:"init_chain_validators_hash"`
	Header1ValidatorsHash     string `json:"header_1_validators_hash"`
	GenesisValidatorLinkPass  bool   `json:"genesis_validator_link_pass"`
	TopLevelGenesisValidators int    `json:"top_level_genesis_validators"`
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

func hx(b []byte) string { return fmt.Sprintf("%X", b) }

func main() {
	configureMainnet()
	if len(os.Args) != 3 {
		fmt.Fprintln(os.Stderr, "usage: initchain_v1 <genesis.json> <block_1.json>")
		os.Exit(2)
	}
	genRaw, err := os.ReadFile(os.Args[1])
	if err != nil {
		panic(err)
	}
	gen, err := tmtypes.GenesisDocFromJSON(genRaw)
	if err != nil {
		panic(err)
	}

	var block1 blockEnvelope
	blockRaw, err := os.ReadFile(os.Args[2])
	if err != nil {
		panic(err)
	}
	if err := tmjson.Unmarshal(blockRaw, &block1); err != nil {
		panic(fmt.Errorf("decode block1: %w", err))
	}
	if block1.Result.Block == nil {
		panic("nil block1")
	}

	home, err := os.MkdirTemp("", "coreum-v1-initchain-")
	if err != nil {
		panic(err)
	}
	defer os.RemoveAll(home)
	if err := os.MkdirAll(filepath.Join(home, "data"), 0o755); err != nil {
		panic(err)
	}

	encoding := coreumconfig.NewEncodingConfig(coreumapp.ModuleBasics)
	application := coreumapp.New(
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

	req := abci.RequestInitChain{
		Time:            gen.GenesisTime,
		ChainId:         gen.ChainID,
		ConsensusParams: tmtypes.TM2PB.ConsensusParams(gen.ConsensusParams),
		AppStateBytes:   gen.AppState,
		InitialHeight:   gen.InitialHeight,
	}
	resp := application.InitChain(req)
	vals, err := tmtypes.PB2TM.ValidatorUpdates(resp.Validators)
	if err != nil {
		panic(err)
	}
	vs := tmtypes.NewValidatorSet(vals)
	headerHash := block1.Result.Block.Header.ValidatorsHash
	out := receipt{
		ChainID:                   gen.ChainID,
		InitialHeight:             gen.InitialHeight,
		InitChainValidatorUpdates: len(resp.Validators),
		InitChainValidatorsHash:   hx(vs.Hash()),
		Header1ValidatorsHash:     hx(headerHash),
		GenesisValidatorLinkPass:  bytes.Equal(vs.Hash(), headerHash),
		TopLevelGenesisValidators: len(gen.Validators),
	}
	b, _ := json.MarshalIndent(out, "", "  ")
	fmt.Println(string(b))
	if !out.GenesisValidatorLinkPass {
		os.Exit(1)
	}
}
