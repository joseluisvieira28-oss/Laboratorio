package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

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
	ChainID                 string `json:"chain_id"`
	Height                  int64  `json:"height"`
	TxCount                 int    `json:"tx_count"`
	AllDeliverTxCodeZero    bool   `json:"all_deliver_tx_code_zero"`
	EndBlockValidatorUpdates int   `json:"end_block_validator_updates"`
	LocalPostBlockAppHash   string `json:"local_post_block_app_hash"`
	HeaderNextAppHash       string `json:"header_next_app_hash"`
	AppHashOffsetPass       bool   `json:"app_hash_offset_pass"`
}

func hx(b []byte) string { return fmt.Sprintf("%X", b) }

func readBlock(path string) *tmtypes.Block {
	raw, err := os.ReadFile(path)
	if err != nil { panic(err) }
	var env blockEnvelope
	if err := tmjson.Unmarshal(raw, &env); err != nil { panic(err) }
	if env.Result.Block == nil { panic("nil block") }
	return env.Result.Block
}

func main() {
	if len(os.Args) != 4 {
		fmt.Fprintln(os.Stderr, "usage: execute_block1_v1 <genesis.json> <block_1.json> <block_2.json>")
		os.Exit(2)
	}
	genRaw, err := os.ReadFile(os.Args[1])
	if err != nil { panic(err) }
	gen, err := tmtypes.GenesisDocFromJSON(genRaw)
	if err != nil { panic(err) }
	b1 := readBlock(os.Args[2])
	b2 := readBlock(os.Args[3])
	if b1.Header.Height != 1 || b2.Header.Height != 2 { panic("expected blocks 1 and 2") }
	if b1.Header.ChainID != gen.ChainID || b2.Header.ChainID != gen.ChainID { panic("chain-id mismatch") }

	home, err := os.MkdirTemp("", "coreum-v1-block1-")
	if err != nil { panic(err) }
	defer os.RemoveAll(home)

	encoding := coreumconfig.NewEncodingConfig(coreumapp.ModuleBasics)
	app := coreumapp.New(
		tmlog.NewNopLogger(), dbm.NewMemDB(), nil, true,
		map[int64]bool{}, home, 0, encoding, opts{},
	)

	app.InitChain(abci.RequestInitChain{
		Time: gen.GenesisTime,
		ChainId: gen.ChainID,
		ConsensusParams: tmtypes.TM2PB.ConsensusParams(gen.ConsensusParams),
		AppStateBytes: gen.AppState,
		InitialHeight: gen.InitialHeight,
	})

	app.BeginBlock(abci.RequestBeginBlock{
		Hash: b1.Hash(),
		Header: b1.Header.ToProto(),
	})

	allOK := true
	for _, tx := range b1.Data.Txs {
		resp := app.DeliverTx(abci.RequestDeliverTx{Tx: tx})
		if resp.Code != 0 { allOK = false }
	}
	end := app.EndBlock(abci.RequestEndBlock{Height: 1})
	commit := app.Commit()
	pass := bytes.Equal(commit.Data, b2.Header.AppHash)
	out := receipt{
		ChainID: gen.ChainID,
		Height: 1,
		TxCount: len(b1.Data.Txs),
		AllDeliverTxCodeZero: allOK,
		EndBlockValidatorUpdates: len(end.ValidatorUpdates),
		LocalPostBlockAppHash: hx(commit.Data),
		HeaderNextAppHash: hx(b2.Header.AppHash),
		AppHashOffsetPass: pass,
	}
	raw, _ := json.MarshalIndent(out, "", "  ")
	fmt.Println(string(raw))
	if !allOK || !pass { os.Exit(1) }
}
