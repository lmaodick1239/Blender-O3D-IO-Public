
/mnt/Random/users/user/Documents/Ghidra/OMSI/Omsi.exe:     file format pei-i386


Disassembly of section .text:

0078fc80 <.text+0x38ec80>:
  78fc80:	05 e8 d6 6c c7       	add    eax,0xc76cd6e8
  78fc85:	ff 8b 04 98 8b 40    	dec    DWORD PTR [ebx+0x408b9804]
  78fc8b:	7c 8b                	jl     0x78fc18
  78fc8d:	55                   	push   ebp
  78fc8e:	f8                   	clc
  78fc8f:	85 c0                	test   eax,eax
  78fc91:	74 05                	je     0x78fc98
  78fc93:	3b 50 fc             	cmp    edx,DWORD PTR [eax-0x4]
  78fc96:	72 05                	jb     0x78fc9d
  78fc98:	e8 bf 6c c7 ff       	call   0x40695c
  78fc9d:	8b 04 90             	mov    eax,DWORD PTR [eax+edx*4]
  78fca0:	b2 01                	mov    dl,0x1
  78fca2:	e8 35 2b e2 ff       	call   0x5b27dc
  78fca7:	ff 45 f8             	inc    DWORD PTR [ebp-0x8]
  78fcaa:	ff 4d f0             	dec    DWORD PTR [ebp-0x10]
  78fcad:	75 c3                	jne    0x78fc72
  78fcaf:	43                   	inc    ebx
  78fcb0:	ff 4d f4             	dec    DWORD PTR [ebp-0xc]
  78fcb3:	0f 85 f9 fe ff ff    	jne    0x78fbb2
  78fcb9:	e9 06 01 00 00       	jmp    0x78fdc4
  78fcbe:	80 7d ff 03          	cmp    BYTE PTR [ebp-0x1],0x3
  78fcc2:	0f 85 fc 00 00 00    	jne    0x78fdc4
  78fcc8:	e8 53 0d 07 00       	call   0x800a20
  78fccd:	a1 e4 8c 85 00       	mov    eax,ds:0x858ce4
  78fcd2:	8b 00                	mov    eax,DWORD PTR [eax]
  78fcd4:	b9 01 00 00 00       	mov    ecx,0x1
  78fcd9:	ba 8f 00 00 00       	mov    edx,0x8f
  78fcde:	e8 9d 10 07 00       	call   0x800d80
  78fce3:	8b 86 18 01 00 00    	mov    eax,DWORD PTR [esi+0x118]
  78fce9:	e8 16 ab c7 ff       	call   0x40a804
  78fcee:	85 c0                	test   eax,eax
  78fcf0:	0f 8c a9 00 00 00    	jl     0x78fd9f
  78fcf6:	40                   	inc    eax
  78fcf7:	89 45 f4             	mov    DWORD PTR [ebp-0xc],eax
  78fcfa:	33 db                	xor    ebx,ebx
  78fcfc:	8b 86 18 01 00 00    	mov    eax,DWORD PTR [esi+0x118]
  78fd02:	85 c0                	test   eax,eax
  78fd04:	74 05                	je     0x78fd0b
  78fd06:	3b 58 fc             	cmp    ebx,DWORD PTR [eax-0x4]
  78fd09:	72 05                	jb     0x78fd10
  78fd0b:	e8 4c 6c c7 ff       	call   0x40695c
  78fd10:	8b 04 98             	mov    eax,DWORD PTR [eax+ebx*4]
  78fd13:	80 78 3d 00          	cmp    BYTE PTR [eax+0x3d],0x0
  78fd17:	75 7c                	jne    0x78fd95
  78fd19:	8b 86 18 01 00 00    	mov    eax,DWORD PTR [esi+0x118]
  78fd1f:	85 c0                	test   eax,eax
  78fd21:	74 05                	je     0x78fd28
  78fd23:	3b 58 fc             	cmp    ebx,DWORD PTR [eax-0x4]
  78fd26:	72 05                	jb     0x78fd2d
  78fd28:	e8 2f 6c c7 ff       	call   0x40695c
  78fd2d:	8b 04 98             	mov    eax,DWORD PTR [eax+ebx*4]
  78fd30:	80 78 38 00          	cmp    BYTE PTR [eax+0x38],0x0
  78fd34:	74 5f                	je     0x78fd95
  78fd36:	8b 86 18 01 00 00    	mov    eax,DWORD PTR [esi+0x118]
  78fd3c:	85 c0                	test   eax,eax
  78fd3e:	74 05                	je     0x78fd45
  78fd40:	3b 58 fc             	cmp    ebx,DWORD PTR [eax-0x4]
  78fd43:	72 05                	jb     0x78fd4a
  78fd45:	e8 12 6c c7 ff       	call   0x40695c
  78fd4a:	8b 04 98             	mov    eax,DWORD PTR [eax+ebx*4]
  78fd4d:	80 b8 d8 00 00 00 00 	cmp    BYTE PTR [eax+0xd8],0x0
  78fd54:	74 3f                	je     0x78fd95
  78fd56:	8b 86 18 01 00 00    	mov    eax,DWORD PTR [esi+0x118]
  78fd5c:	85 c0                	test   eax,eax
  78fd5e:	74 05                	je     0x78fd65
  78fd60:	3b 58 fc             	cmp    ebx,DWORD PTR [eax-0x4]
  78fd63:	72 05                	jb     0x78fd6a
  78fd65:	e8 f2 6b c7 ff       	call   0x40695c
  78fd6a:	8b 04 98             	mov    eax,DWORD PTR [eax+ebx*4]
  78fd6d:	8d 90 f8 00 00 00    	lea    edx,[eax+0xf8]
  78fd73:	8b 86 18 01 00 00    	mov    eax,DWORD PTR [esi+0x118]
  78fd79:	85 c0                	test   eax,eax
  78fd7b:	74 05                	je     0x78fd82
  78fd7d:	3b 58 fc             	cmp    ebx,DWORD PTR [eax-0x4]
  78fd80:	72 05                	jb     0x78fd87
  78fd82:	e8 d5 6b c7 ff       	call   0x40695c
  78fd87:	8b 04 98             	mov    eax,DWORD PTR [eax+ebx*4]
  78fd8a:	8b 80 84 00 00 00    	mov    eax,DWORD PTR [eax+0x84]
  78fd90:	e8 23 5a fe ff       	call   0x7757b8
  78fd95:	43                   	inc    ebx
  78fd96:	ff 4d f4             	dec    DWORD PTR [ebp-0xc]
  78fd99:	0f 85 5d ff ff ff    	jne    0x78fcfc
  78fd9f:	a1 e4 8c 85 00       	mov    eax,ds:0x858ce4
  78fda4:	8b 00                	mov    eax,DWORD PTR [eax]
  78fda6:	33 c9                	xor    ecx,ecx
  78fda8:	ba 8f 00 00 00       	mov    edx,0x8f
  78fdad:	e8 ce 0f 07 00       	call   0x800d80
  78fdb2:	a1 dc 8b 85 00       	mov    eax,ds:0x858bdc
  78fdb7:	8b 00                	mov    eax,DWORD PTR [eax]
  78fdb9:	8b 80 74 01 00 00    	mov    eax,DWORD PTR [eax+0x174]
  78fdbf:	e8 d0 7d e8 ff       	call   0x617b94
  78fdc4:	b8 5e 00 00 00       	mov    eax,0x5e
  78fdc9:	e8 aa 5e 07 00       	call   0x805c78
  78fdce:	84 c0                	test   al,al
  78fdd0:	74 0b                	je     0x78fddd
  78fdd2:	0f b6 55 ff          	movzx  edx,BYTE PTR [ebp-0x1]
  78fdd6:	8b c6                	mov    eax,esi
  78fdd8:	e8 0f ed ff ff       	call   0x78eaec
  78fddd:	a1 1c 89 85 00       	mov    eax,ds:0x85891c
  78fde2:	0f b6 00             	movzx  eax,BYTE PTR [eax]
  78fde5:	8b 15 e0 9d 85 00    	mov    edx,DWORD PTR ds:0x859de0
  78fdeb:	88 02                	mov    BYTE PTR [edx],al
  78fded:	33 c0                	xor    eax,eax
  78fdef:	5a                   	pop    edx
  78fdf0:	59                   	pop    ecx
  78fdf1:	59                   	pop    ecx
  78fdf2:	64 89 10             	mov    DWORD PTR fs:[eax],edx
  78fdf5:	68 28 fe 78 00       	push   0x78fe28
  78fdfa:	8d 45 80             	lea    eax,[ebp-0x80]
  78fdfd:	8b                   	.byte 0x8b
  78fdfe:	15                   	.byte 0x15
  78fdff:	c4                   	.byte 0xc4
