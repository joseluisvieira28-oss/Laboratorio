"""Minimal Ethereum Keccak-256 for ABI event signatures (no dependencies)."""
RC = [0x0000000000000001,0x0000000000008082,0x800000000000808A,0x8000000080008000,
0x000000000000808B,0x0000000080000001,0x8000000080008081,0x8000000000008009,
0x000000000000008A,0x0000000000000088,0x0000000080008009,0x000000008000000A,
0x000000008000808B,0x800000000000008B,0x8000000000008089,0x8000000000008003,
0x8000000000008002,0x8000000000000080,0x000000000000800A,0x800000008000000A,
0x8000000080008081,0x8000000000008080,0x0000000080000001,0x8000000080008008]
ROT = [[0,36,3,41,18],[1,44,10,45,2],[62,6,43,15,61],[28,55,25,21,56],[27,20,39,8,14]]
MASK = (1<<64)-1
def rol(v,n): return ((v<<n)|(v>>(64-n)))&MASK if n else v
def keccak(data):
    data = bytearray(data); data.append(1)
    data.extend(b'\0'*((136-len(data)%136)%136)); data[-1] |= 128
    a = [0]*25
    for start in range(0,len(data),136):
        chunk=data[start:start+136]
        for i in range(17): a[i]^=int.from_bytes(chunk[i*8:i*8+8],'little')
        for rc in RC:
            c=[a[x]^a[x+5]^a[x+10]^a[x+15]^a[x+20] for x in range(5)]
            d=[c[(x-1)%5]^rol(c[(x+1)%5],1) for x in range(5)]
            for x in range(5):
                for y in range(5): a[x+5*y]^=d[x]
            b=[0]*25
            for x in range(5):
                for y in range(5): b[y+5*((2*x+3*y)%5)]=rol(a[x+5*y],ROT[x][y])
            for x in range(5):
                for y in range(5): a[x+5*y]=b[x+5*y]^((~b[(x+1)%5+5*y])&b[(x+2)%5+5*y])
            a[0]^=rc
    return '0x'+b''.join(x.to_bytes(8,'little') for x in a)[:32].hex()

if __name__=='__main__':
    assert keccak(b'')=='0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'
    assert keccak(b'Transfer(address,address,uint256)')=='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
    print(keccak(b'PairCreated(address,address,address,uint256)'))
    print(keccak(b'PoolCreated(address,address,uint24,int24,address)'))
