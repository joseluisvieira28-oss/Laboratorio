package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	tmjson "github.com/tendermint/tendermint/libs/json"
	coretypes "github.com/tendermint/tendermint/rpc/core/types"
	tmtypes "github.com/tendermint/tendermint/types"
)

type blockEnvelope struct {
	Result coretypes.ResultBlock `json:"result"`
}
type commitEnvelope struct {
	Result coretypes.ResultCommit `json:"result"`
}
type validatorsEnvelope struct {
	Result coretypes.ResultValidators `json:"result"`
}
type receipt struct {
	Height                  int64  `json:"height"`
	ChainID                 string `json:"chain_id"`
	Time                    string `json:"time"`
	ReportedBlockHash       string `json:"reported_block_hash"`
	ComputedBlockHash       string `json:"computed_block_hash"`
	HeaderDataHash          string `json:"header_data_hash"`
	ComputedDataHash        string `json:"computed_data_hash"`
	HeaderValidatorsHash    string `json:"header_validators_hash"`
	ComputedValidatorsHash  string `json:"computed_validators_hash"`
	HeaderNextValidatorsHash string `json:"header_next_validators_hash"`
	ComputedNextValidatorsHash string `json:"computed_next_validators_hash"`
	AppHash                 string `json:"app_hash"`
	CommitVerified          bool   `json:"commit_verified"`
	BlockHashVerified       bool   `json:"block_hash_verified"`
	DataHashVerified        bool   `json:"data_hash_verified"`
	ValidatorsHashVerified  bool   `json:"validators_hash_verified"`
	NextValidatorsHashVerified bool `json:"next_validators_hash_verified"`
}

func readTM(path string, v any) error {
	b, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	return tmjson.Unmarshal(b, v)
}
func hx(b []byte) string { return fmt.Sprintf("%X", b) }

func main() {
	if len(os.Args) != 5 {
		fmt.Fprintln(os.Stderr, "usage: blockprobe <block.json> <commit.json> <validators.json> <next_validators.json>")
		os.Exit(2)
	}
	var b blockEnvelope
	var c commitEnvelope
	var v validatorsEnvelope
	var nv validatorsEnvelope
	for _, item := range []struct {
		path string
		dst  any
	}{{os.Args[1], &b}, {os.Args[2], &c}, {os.Args[3], &v}, {os.Args[4], &nv}} {
		if err := readTM(item.path, item.dst); err != nil {
			panic(fmt.Errorf("decode %s: %w", item.path, err))
		}
	}
	if b.Result.Block == nil {
		panic("nil block")
	}
	h := b.Result.Block.Header.Height
	if v.Result.BlockHeight != h {
		panic(fmt.Errorf("validator response height=%d block height=%d", v.Result.BlockHeight, h))
	}
	if nv.Result.BlockHeight != h+1 {
		panic(fmt.Errorf("next validator response height=%d want=%d", nv.Result.BlockHeight, h+1))
	}
	computedBlock := b.Result.Block.Hash()
	computedData := b.Result.Block.Data.Hash()
	vs := tmtypes.NewValidatorSet(v.Result.Validators)
	nvs := tmtypes.NewValidatorSet(nv.Result.Validators)
	if c.Result.Commit == nil || c.Result.Header == nil {
		panic("nil signed header/commit")
	}
	commitErr := vs.VerifyCommit(b.Result.Block.Header.ChainID, b.Result.BlockID, h, c.Result.Commit)
	r := receipt{
		Height: h,
		ChainID: b.Result.Block.Header.ChainID,
		Time: b.Result.Block.Header.Time.UTC().Format("2006-01-02T15:04:05.999999999Z"),
		ReportedBlockHash: hx(b.Result.BlockID.Hash),
		ComputedBlockHash: hx(computedBlock),
		HeaderDataHash: hx(b.Result.Block.Header.DataHash),
		ComputedDataHash: hx(computedData),
		HeaderValidatorsHash: hx(b.Result.Block.Header.ValidatorsHash),
		ComputedValidatorsHash: hx(vs.Hash()),
		HeaderNextValidatorsHash: hx(b.Result.Block.Header.NextValidatorsHash),
		ComputedNextValidatorsHash: hx(nvs.Hash()),
		AppHash: hx(b.Result.Block.Header.AppHash),
		CommitVerified: commitErr == nil,
		BlockHashVerified: bytes.Equal(computedBlock, b.Result.BlockID.Hash),
		DataHashVerified: bytes.Equal(computedData, b.Result.Block.Header.DataHash),
		ValidatorsHashVerified: bytes.Equal(vs.Hash(), b.Result.Block.Header.ValidatorsHash),
		NextValidatorsHashVerified: bytes.Equal(nvs.Hash(), b.Result.Block.Header.NextValidatorsHash),
	}
	if !r.BlockHashVerified || !r.DataHashVerified || !r.ValidatorsHashVerified || !r.NextValidatorsHashVerified || !r.CommitVerified {
		out, _ := json.MarshalIndent(r, "", "  ")
		fmt.Println(string(out))
		if commitErr != nil {
			fmt.Fprintln(os.Stderr, "commit verification:", commitErr)
		}
		os.Exit(1)
	}
	out, _ := json.MarshalIndent(r, "", "  ")
	fmt.Println(string(out))
}
