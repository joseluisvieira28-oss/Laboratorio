package main

import (
 "bytes"
 "encoding/base64"
 "encoding/hex"
 "encoding/json"
 "fmt"
 "os"
 "path/filepath"
 ics23 "github.com/cosmos/ics23/go"
)

type Op struct { Type string `json:"type"`; Data string `json:"data"` }
type Step struct { Cursor string `json:"cursor_hex"`; Next *string `json:"next_key_hex"`; Value *string `json:"value_base64"`; Ops []Op `json:"proof_ops"` }
type Input struct { Chain string `json:"chain"`; Provider string `json:"provider"`; Height int `json:"height"`; Header struct { Height int `json:"height"`; AppHash string `json:"app_hash"` } `json:"canonical_next_header"`; Steps []Step `json:"steps"`; Terminal bool `json:"terminal"` }
func decode(s string) []byte { b,e:=base64.StdEncoding.DecodeString(s);if e!=nil {panic(e)};return b }
func check(in Input) error {
 if in.Header.Height!=in.Height+1 || len(in.Steps)==0 {return fmt.Errorf("missing canonical next header or proofs")}
 appRoot,err:=hex.DecodeString(in.Header.AppHash);if err!=nil{return err}
 cursor:=[]byte{0x41};var commonRoot []byte
 for _,s:=range in.Steps {
  got,e:=hex.DecodeString(s.Cursor);if e!=nil || !bytes.Equal(got,cursor){return fmt.Errorf("cursor discontinuity")}
  if len(s.Ops)!=2 || s.Ops[0].Type!="ics23:iavl" || s.Ops[1].Type!="ics23:simple" {return fmt.Errorf("unknown proof types")}
  proof:=new(ics23.CommitmentProof);if e=proof.Unmarshal(decode(s.Ops[0].Data));e!=nil{return e}
  root,e:=proof.Calculate();if e!=nil{return e}
  if commonRoot!=nil && !bytes.Equal(commonRoot,root){return fmt.Errorf("store root changed")};commonRoot=root
  if !ics23.VerifyNonMembership(ics23.IavlSpec,root,proof,cursor){return fmt.Errorf("invalid nonmembership or adjacency")}
  top:=new(ics23.CommitmentProof);if e=top.Unmarshal(decode(s.Ops[1].Data));e!=nil{return e}
  if !ics23.VerifyMembership(ics23.TendermintSpec,appRoot,top,[]byte("staking"),root){return fmt.Errorf("historical app-root binding failed")}
  // Negative control: the same proof MUST fail against a changed app root.
  bad:=append([]byte(nil),appRoot...);bad[0]^=1
  if ics23.VerifyMembership(ics23.TendermintSpec,bad,top,[]byte("staking"),root){return fmt.Errorf("tampered root accepted")}
  np:=proof.GetNonexist();if np==nil{return fmt.Errorf("not absence proof")};right:=np.Right
  if right==nil {
   if s.Next!=nil || !in.Terminal{return fmt.Errorf("unproven terminal")};cursor=nil;continue
  }
  if s.Next==nil{return fmt.Errorf("missing neighbor key")};nk,e:=hex.DecodeString(*s.Next);if e!=nil || !bytes.Equal(nk,right.Key){return fmt.Errorf("neighbor key mismatch")}
  if s.Value==nil || !bytes.Equal(decode(*s.Value),right.Value){return fmt.Errorf("neighbor value mismatch")}
  membership:=&ics23.CommitmentProof{Proof:&ics23.CommitmentProof_Exist{Exist:right}}
  if !ics23.VerifyMembership(ics23.IavlSpec,root,membership,nk,right.Value){return fmt.Errorf("neighbor membership invalid")}
  if !bytes.HasPrefix(nk,[]byte{0x41}) {if !in.Terminal{return fmt.Errorf("terminal flag mismatch")};cursor=nil;continue}
  cursor=append(append([]byte(nil),nk...),0)
 }
 if in.Terminal && cursor!=nil{return fmt.Errorf("false terminal flag")}
 return nil
}
func main(){
 dir:=os.Args[1];paths,_:=filepath.Glob(filepath.Join(dir,"proof-queue-*.json"));rows:=[]map[string]interface{}{}
 for _,p:=range paths {
  raw,e:=os.ReadFile(p);if e!=nil{panic(e)};var in Input;if e=json.Unmarshal(raw,&in);e!=nil{panic(e)}
  e=check(in);row:=map[string]interface{}{"file":filepath.Base(p),"chain":in.Chain,"provider":in.Provider,"height":in.Height,"verified_steps":len(in.Steps),"proof_verified":e==nil,"full_prefix_complete":e==nil&&in.Terminal,"tampered_root_rejected":e==nil}
  if e!=nil{row["error"]=e.Error()};rows=append(rows,row)
 }
 out:=map[string]interface{}{"ics23_version":"v0.10.0","ics23_commit":"74ce807b7be39a7e0afb4e2efb8e28a57965f57b","market_outcomes_opened":false,"rows":rows}
 raw,e:=json.MarshalIndent(out,"","  ");if e!=nil{panic(e)};fmt.Println(string(raw));if e=os.WriteFile(filepath.Join(dir,"proof-verification.json"),append(raw,'\n'),0644);e!=nil{panic(e)}
}
