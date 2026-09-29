#include <bits/stdc++.h>
using namespace std;

static pair<long long,long long> median2_mad4(const vector<long long>& src){
    vector<long long> w=src;
    int n=(int)w.size(),k=n/2;
    nth_element(w.begin(),w.begin()+k,w.end());
    long long hi=w[k],m2;
    if(n%2) m2=2*hi;
    else { long long lo=*max_element(w.begin(),w.begin()+k); m2=lo+hi; }
    vector<long long> d; d.reserve(n);
    for(long long x:src) d.push_back(llabs(2*x-m2));
    nth_element(d.begin(),d.begin()+k,d.end());
    long long dhi=d[k],mad4;
    if(n%2) mad4=2*dhi;
    else { long long dlo=*max_element(d.begin(),d.begin()+k); mad4=dlo+dhi; }
    return {m2,mad4};
}

int main(){
    ios::sync_with_stdio(false);
    ifstream ff("artifacts/discovery/flow.txt"), fr("artifacts/discovery/relret4.txt"), fo("artifacts/discovery/offsets.csv");
    vector<long long> base; long long q; while(ff>>q) base.push_back(q);
    vector<double> ret; string line;
    while(getline(fr,line)){ if(line.empty())continue; if(line=="nan"||line=="NaN") ret.push_back(numeric_limits<double>::quiet_NaN()); else ret.push_back(stod(line)); }
    if(base.size()!=5880 || ret.size()!=5880){ cerr<<"INPUT_SIZE_FAIL\n"; return 2; }
    vector<int> starts={0,744,1464,2208,2952,3672,4416,5136};
    vector<int> lens={744,720,744,744,720,744,720,744};
    vector<array<int,8>> offsets; 
    while(getline(fo,line)){
        if(line.empty())continue; array<int,8>a{}; stringstream ss(line); string t; int j=0;
        while(getline(ss,t,',')){ if(j<8)a[j++]=stoi(t); }
        if(j!=8){cerr<<"OFFSET_PARSE_FAIL\n";return 2;} offsets.push_back(a);
    }
    if(offsets.size()!=10000){cerr<<"OFFSET_COUNT_FAIL\n";return 2;}
    ofstream out("artifacts/discovery/null_stats.csv");
    out<<"perm,null_stat,eligible_triggers,all_independent_triggers\n";
    vector<long long>a(base.size());
    for(size_t p=0;p<offsets.size();p++){
        for(int m=0;m<8;m++){
            int s=starts[m],n=lens[m],k=offsets[p][m];
            for(int i=0;i<n;i++) a[s+(i+k)%n]=base[s+i];
        }
        int last=-100000,alltr=0,eligible=0; long double sum=0;
        for(int i=672;i<(int)a.size();i++){
            int lo=max(0,i-720);
            vector<long long>w(a.begin()+lo,a.begin()+i);
            auto [m2,mad4]=median2_mad4(w);
            if(mad4==0) continue;
            long double z=2.0L*(2.0L*a[i]-m2)/(1.4826L*mad4);
            if(fabsl(z)>=3.0L && i-last>6){
                alltr++; last=i;
                if(isfinite(ret[i])){
                    eligible++;
                    sum+=(z>0?1.0L:-1.0L)*(long double)ret[i];
                }
            }
        }
        if(eligible==0) out<<p<<",nan,0,"<<alltr<<"\n";
        else out<<p<<","<<setprecision(17)<<(double)(sum/eligible)<<","<<eligible<<","<<alltr<<"\n";
    }
    return 0;
}
