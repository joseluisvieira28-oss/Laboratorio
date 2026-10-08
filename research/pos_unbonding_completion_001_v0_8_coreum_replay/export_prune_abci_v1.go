package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"

	tmstate "github.com/tendermint/tendermint/proto/tendermint/state"
	dbm "github.com/tendermint/tm-db"
)

type row struct {
	Height int64 `json:"height"`
	File string `json:"file"`
	Bytes int `json:"bytes"`
	SHA256 string `json:"sha256"`
	TxResponses int `json:"tx_responses"`
}

func main(){
	if len(os.Args)!=5{
		fmt.Fprintln(os.Stderr,"usage: export_prune_abci_v1 <state_db_dir> <out_dir> <start_height> <end_height>")
		os.Exit(2)
	}
	dbDir,outDir:=os.Args[1],os.Args[2]
	start,err:=strconv.ParseInt(os.Args[3],10,64);if err!=nil{panic(err)}
	end,err:=strconv.ParseInt(os.Args[4],10,64);if err!=nil||start<1||end<start{panic("invalid range")}
	if err:=os.MkdirAll(outDir,0755);err!=nil{panic(err)}
	db,err:=dbm.NewGoLevelDB("state",dbDir);if err!=nil{panic(err)};defer db.Close()

	rows:=make([]row,0,end-start+1)
	for h:=start;h<=end;h++{
		key:=[]byte(fmt.Sprintf("abciResponsesKey:%d",h))
		raw,err:=db.Get(key);if err!=nil{panic(err)}
		if len(raw)==0{panic(fmt.Sprintf("missing local ABCI response H=%d",h))}
		var resp tmstate.ABCIResponses
		if err:=resp.Unmarshal(raw);err!=nil{panic(fmt.Sprintf("invalid local ABCI response H=%d: %v",h,err))}
		if resp.BeginBlock==nil||resp.EndBlock==nil{panic(fmt.Sprintf("incomplete local ABCI response H=%d",h))}
		name:=fmt.Sprintf("abci_%d.pb",h)
		p:=filepath.Join(outDir,name)
		if err:=os.WriteFile(p,raw,0644);err!=nil{panic(err)}
		check,err:=os.ReadFile(p);if err!=nil{panic(err)}
		s:=sha256.Sum256(raw);s2:=sha256.Sum256(check)
		if s!=s2{panic(fmt.Sprintf("post-write hash mismatch H=%d",h))}
		rows=append(rows,row{Height:h,File:name,Bytes:len(raw),SHA256:hex.EncodeToString(s[:]),TxResponses:len(resp.DeliverTxs)})
	}

	lastRaw,err:=db.Get([]byte("lastABCIResponseKey"));if err!=nil{panic(err)}
	if len(lastRaw)==0{panic("lastABCIResponseKey missing")}
	var info tmstate.ABCIResponsesInfo
	if err:=info.Unmarshal(lastRaw);err!=nil{panic(err)}
	if info.Height!=end{panic(fmt.Sprintf("last ABCI height=%d want=%d",info.Height,end))}

	manifest:=map[string]interface{}{
		"schema":"coreum-v08-local-abci-export-v1",
		"start_height":start,"end_height":end,"record_count":len(rows),
		"records":rows,"last_abci_response_height":info.Height,
		"exact_db_values_exported":true,"block_results_consumed_from_rpc":false,
		"census_executed":false,"market_outcomes_opened":false,
	}
	b,_:=json.MarshalIndent(manifest,"","  ")
	manifestPath:=filepath.Join(outDir,fmt.Sprintf("abci_%d_%d.manifest.json",start,end))
	if err:=os.WriteFile(manifestPath,append(b,'\n'),0644);err!=nil{panic(err)}

	batch:=db.NewBatch();defer batch.Close()
	for h:=start;h<=end;h++{
		if err:=batch.Delete([]byte(fmt.Sprintf("abciResponsesKey:%d",h)));err!=nil{panic(err)}
	}
	if err:=batch.WriteSync();err!=nil{panic(err)}
	for h:=start;h<=end;h++{
		raw,err:=db.Get([]byte(fmt.Sprintf("abciResponsesKey:%d",h)));if err!=nil{panic(err)}
		if len(raw)!=0{panic(fmt.Sprintf("prune verification failed H=%d",h))}
	}
	lastAfter,err:=db.Get([]byte("lastABCIResponseKey"));if err!=nil{panic(err)}
	if len(lastAfter)==0{panic("lastABCIResponseKey lost during prune")}

	fmt.Printf("{\"start_height\":%d,\"end_height\":%d,\"exported\":%d,\"pruned\":%d,\"last_abci_preserved\":true,\"pass\":true}\n",start,end,len(rows),len(rows))
}
