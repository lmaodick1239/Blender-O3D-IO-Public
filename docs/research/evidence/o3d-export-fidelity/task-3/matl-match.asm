
/mnt/Random/users/user/Documents/Ghidra/OMSI/Omsi.exe:     file format pei-i386


Disassembly of section .text:

007c3eb0 <.text+0x3c2eb0>:
  7c3eb0:	55                   	push   ebp
  7c3eb1:	8b ec                	mov    ebp,esp
  7c3eb3:	83 c4 e0             	add    esp,0xffffffe0
  7c3eb6:	53                   	push   ebx
  7c3eb7:	56                   	push   esi
  7c3eb8:	57                   	push   edi
  7c3eb9:	33 db                	xor    ebx,ebx
  7c3ebb:	89 5d ec             	mov    DWORD PTR [ebp-0x14],ebx
  7c3ebe:	89 5d e4             	mov    DWORD PTR [ebp-0x1c],ebx
  7c3ec1:	89 5d e0             	mov    DWORD PTR [ebp-0x20],ebx
  7c3ec4:	89 5d e8             	mov    DWORD PTR [ebp-0x18],ebx
  7c3ec7:	89 4d f8             	mov    DWORD PTR [ebp-0x8],ecx
  7c3eca:	89 55 fc             	mov    DWORD PTR [ebp-0x4],edx
  7c3ecd:	8b f8                	mov    edi,eax
  7c3ecf:	8b 45 fc             	mov    eax,DWORD PTR [ebp-0x4]
  7c3ed2:	e8 75 49 c4 ff       	call   0x40884c
  7c3ed7:	33 c0                	xor    eax,eax
  7c3ed9:	55                   	push   ebp
  7c3eda:	68 95 3f 7c 00       	push   0x7c3f95
  7c3edf:	64 ff 30             	push   DWORD PTR fs:[eax]
  7c3ee2:	64 89 20             	mov    DWORD PTR fs:[eax],esp
  7c3ee5:	c7 45 f4 ff ff ff ff 	mov    DWORD PTR [ebp-0xc],0xffffffff
  7c3eec:	33 c0                	xor    eax,eax
  7c3eee:	89 45 f0             	mov    DWORD PTR [ebp-0x10],eax
  7c3ef1:	8b 87 ec 00 00 00    	mov    eax,DWORD PTR [edi+0xec]
  7c3ef7:	e8 08 69 c4 ff       	call   0x40a804
  7c3efc:	8b d8                	mov    ebx,eax
  7c3efe:	85 db                	test   ebx,ebx
  7c3f00:	7c 70                	jl     0x7c3f72
  7c3f02:	43                   	inc    ebx
  7c3f03:	33 f6                	xor    esi,esi
  7c3f05:	8d 45 e8             	lea    eax,[ebp-0x18]
  7c3f08:	8b 97 f0 00 00 00    	mov    edx,DWORD PTR [edi+0xf0]
  7c3f0e:	85 d2                	test   edx,edx
  7c3f10:	74 05                	je     0x7c3f17
  7c3f12:	3b 72 fc             	cmp    esi,DWORD PTR [edx-0x4]
  7c3f15:	72 05                	jb     0x7c3f1c
  7c3f17:	e8 40 2a c4 ff       	call   0x40695c
  7c3f1c:	8b 14 b2             	mov    edx,DWORD PTR [edx+esi*4]
  7c3f1f:	e8 d0 56 c4 ff       	call   0x4095f4
  7c3f24:	8b 45 e8             	mov    eax,DWORD PTR [ebp-0x18]
  7c3f27:	8d 55 ec             	lea    edx,[ebp-0x14]
  7c3f2a:	e8 95 d4 c5 ff       	call   0x4213c4
  7c3f2f:	8b 45 ec             	mov    eax,DWORD PTR [ebp-0x14]
  7c3f32:	50                   	push   eax
  7c3f33:	8d 45 e0             	lea    eax,[ebp-0x20]
  7c3f36:	8b 55 fc             	mov    edx,DWORD PTR [ebp-0x4]
  7c3f39:	e8 b6 56 c4 ff       	call   0x4095f4
  7c3f3e:	8b 45 e0             	mov    eax,DWORD PTR [ebp-0x20]
  7c3f41:	8d 55 e4             	lea    edx,[ebp-0x1c]
  7c3f44:	e8 7b d4 c5 ff       	call   0x4213c4
  7c3f49:	8b 55 e4             	mov    edx,DWORD PTR [ebp-0x1c]
  7c3f4c:	58                   	pop    eax
  7c3f4d:	e8 ce 59 c4 ff       	call   0x409920
  7c3f52:	75 1a                	jne    0x7c3f6e
  7c3f54:	8b 45 f0             	mov    eax,DWORD PTR [ebp-0x10]
  7c3f57:	3b 45 f8             	cmp    eax,DWORD PTR [ebp-0x8]
  7c3f5a:	7d 0d                	jge    0x7c3f69
  7c3f5c:	83 45 f0 01          	add    DWORD PTR [ebp-0x10],0x1
  7c3f60:	71 0c                	jno    0x7c3f6e
  7c3f62:	e8 fd 29 c4 ff       	call   0x406964
  7c3f67:	eb 05                	jmp    0x7c3f6e
  7c3f69:	89 75 f4             	mov    DWORD PTR [ebp-0xc],esi
  7c3f6c:	eb 04                	jmp    0x7c3f72
  7c3f6e:	46                   	inc    esi
  7c3f6f:	4b                   	dec    ebx
  7c3f70:	75 93                	jne    0x7c3f05
  7c3f72:	33 c0                	xor    eax,eax
  7c3f74:	5a                   	pop    edx
  7c3f75:	59                   	pop    ecx
  7c3f76:	59                   	pop    ecx
  7c3f77:	64 89 10             	mov    DWORD PTR fs:[eax],edx
  7c3f7a:	68 9c 3f 7c 00       	push   0x7c3f9c
  7c3f7f:	8d 45 e0             	lea    eax,[ebp-0x20]
  7c3f82:	ba 04 00 00 00       	mov    edx,0x4
  7c3f87:	e8 2c 48 c4 ff       	call   0x4087b8
  7c3f8c:	8d 45 fc             	lea    eax,[ebp-0x4]
  7c3f8f:	e8 e8 47 c4 ff       	call   0x40877c
  7c3f94:	c3                   	ret
  7c3f95:	e9 12 3e c4 ff       	jmp    0x407dac
  7c3f9a:	eb e3                	jmp    0x7c3f7f
  7c3f9c:	8b 45 f4             	mov    eax,DWORD PTR [ebp-0xc]
  7c3f9f:	5f                   	pop    edi
  7c3fa0:	5e                   	pop    esi
  7c3fa1:	5b                   	pop    ebx
  7c3fa2:	8b e5                	mov    esp,ebp
  7c3fa4:	5d                   	pop    ebp
  7c3fa5:	c3                   	ret
