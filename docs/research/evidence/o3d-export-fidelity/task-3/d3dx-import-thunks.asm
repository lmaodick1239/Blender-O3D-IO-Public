
/mnt/Random/users/user/Documents/Ghidra/OMSI/Omsi.exe:     file format pei-i386


Disassembly of section .text:

00567e78 <.text+0x166e78>:
  567e78:	ff 25 9c 48 86 00    	jmp    DWORD PTR ds:0x86489c
  567e7e:	8b c0                	mov    eax,eax
  567e80:	ff 25 98 48 86 00    	jmp    DWORD PTR ds:0x864898
  567e86:	8b c0                	mov    eax,eax
  567e88:	ff 25 94 48 86 00    	jmp    DWORD PTR ds:0x864894
  567e8e:	8b c0                	mov    eax,eax
  567e90:	ff 25 94 48 86 00    	jmp    DWORD PTR ds:0x864894
  567e96:	8b c0                	mov    eax,eax
  567e98:	ff 25 90 48 86 00    	jmp    DWORD PTR ds:0x864890
  567e9e:	8b c0                	mov    eax,eax
  567ea0:	ff 25 8c 48 86 00    	jmp    DWORD PTR ds:0x86488c
  567ea6:	8b c0                	mov    eax,eax
  567ea8:	ff 25 88 48 86 00    	jmp    DWORD PTR ds:0x864888
  567eae:	8b c0                	mov    eax,eax
  567eb0:	ff 25 88 48 86 00    	jmp    DWORD PTR ds:0x864888
  567eb6:	8b c0                	mov    eax,eax
  567eb8:	ff 25 84 48 86 00    	jmp    DWORD PTR ds:0x864884
  567ebe:	8b c0                	mov    eax,eax
  567ec0:	ff 25 80 48 86 00    	jmp    DWORD PTR ds:0x864880
  567ec6:	8b c0                	mov    eax,eax
  567ec8:	ff 25 7c 48 86 00    	jmp    DWORD PTR ds:0x86487c
  567ece:	8b c0                	mov    eax,eax
  567ed0:	ff 25 78 48 86 00    	jmp    DWORD PTR ds:0x864878
  567ed6:	8b c0                	mov    eax,eax
  567ed8:	ff 25 74 48 86 00    	jmp    DWORD PTR ds:0x864874
  567ede:	8b c0                	mov    eax,eax
  567ee0:	ff 25 70 48 86 00    	jmp    DWORD PTR ds:0x864870
  567ee6:	8b c0                	mov    eax,eax
  567ee8:	ff 25 6c 48 86 00    	jmp    DWORD PTR ds:0x86486c
  567eee:	8b c0                	mov    eax,eax
  567ef0:	ff 25 68 48 86 00    	jmp    DWORD PTR ds:0x864868
  567ef6:	8b c0                	mov    eax,eax
  567ef8:	ff 25 64 48 86 00    	jmp    DWORD PTR ds:0x864864
  567efe:	8b c0                	mov    eax,eax
  567f00:	ff 25 60 48 86 00    	jmp    DWORD PTR ds:0x864860
  567f06:	8b c0                	mov    eax,eax
  567f08:	ff 25 5c 48 86 00    	jmp    DWORD PTR ds:0x86485c
  567f0e:	8b c0                	mov    eax,eax
  567f10:	ff 25 58 48 86 00    	jmp    DWORD PTR ds:0x864858
  567f16:	8b c0                	mov    eax,eax
  567f18:	ff 25 54 48 86 00    	jmp    DWORD PTR ds:0x864854
  567f1e:	8b c0                	mov    eax,eax
  567f20:	ff 25 50 48 86 00    	jmp    DWORD PTR ds:0x864850
  567f26:	8b c0                	mov    eax,eax
  567f28:	ff 25 4c 48 86 00    	jmp    DWORD PTR ds:0x86484c
  567f2e:	8b c0                	mov    eax,eax
  567f30:	ff 25 48 48 86 00    	jmp    DWORD PTR ds:0x864848
  567f36:	8b c0                	mov    eax,eax
  567f38:	ff 25 44 48 86 00    	jmp    DWORD PTR ds:0x864844
  567f3e:	00 00                	add    BYTE PTR [eax],al
  567f40:	44                   	inc    esp
  567f41:	7f 56                	jg     0x567f99
  567f43:	00 0f                	add    BYTE PTR [edi],cl
  567f45:	0b 49 44             	or     ecx,DWORD PTR [ecx+0x44]
  567f48:	33 44 58 42          	xor    eax,DWORD PTR [eax+ebx*2+0x42]
  567f4c:	75 66                	jne    0x567fb4
  567f4e:	66 65 72 9c          	data16 gs jb 0x567eee
  567f52:	1d 40 00 01 7e       	sbb    eax,0x7e010040
  567f57:	6a 2e                	push   0x2e
  567f59:	93                   	xchg   ebx,eax
  567f5a:	8e c6                	mov    es,esi
  567f5c:	dd 45 a7             	fld    QWORD PTR [ebp-0x59]
  567f5f:	bf 53 d1 9c 86       	mov    edi,0x869cd153
  567f64:	db 1f                	fistp  DWORD PTR [edi]
  567f66:	05 64 33 64 78       	add    eax,0x78643364
  567f6b:	39 02                	cmp    DWORD PTR [edx],eax
  567f6d:	00 ff                	add    bh,bh
  567f6f:	ff 02                	inc    DWORD PTR [edx]
  567f71:	00 00                	add    BYTE PTR [eax],al
  567f73:	00 78 7f             	add    BYTE PTR [eax+0x7f],bh
  567f76:	56                   	push   esi
  567f77:	00 0f                	add    BYTE PTR [edi],cl
  567f79:	09 49 44             	or     DWORD PTR [ecx+0x44],ecx
  567f7c:	33 44 58 46          	xor    eax,DWORD PTR [eax+ebx*2+0x46]
  567f80:	6f                   	outs   dx,DWORD PTR ds:[esi]
  567f81:	6e                   	outs   dx,BYTE PTR ds:[esi]
  567f82:	74 9c                	je     0x567f20
  567f84:	1d 40 00 01 36       	sbb    eax,0x36010040
  567f89:	15 8d 0b ec 9e       	adc    eax,0x9eec0b8d
  567f8e:	b0 49                	mov    al,0x49
  567f90:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  567f91:	ad                   	lods   eax,DWORD PTR ds:[esi]
  567f92:	93                   	xchg   ebx,eax
  567f93:	cf                   	iret
  567f94:	63 af b7 c6 05 64    	arpl   WORD PTR [edi+0x6405c6b7],ebp
  567f9a:	33 64 78 39          	xor    esp,DWORD PTR [eax+edi*2+0x39]
  567f9e:	0d 00 ff ff 02       	or     eax,0x2ffff00
  567fa3:	00 ff                	add    bh,bh
  567fa5:	25 40 48 86 00       	and    eax,0x864840
  567faa:	00 00                	add    BYTE PTR [eax],al
  567fac:	b0 7f                	mov    al,0x7f
  567fae:	56                   	push   esi
  567faf:	00 0f                	add    BYTE PTR [edi],cl
  567fb1:	0d 49 44 33 44       	or     eax,0x44334449
  567fb6:	58                   	pop    eax
  567fb7:	42                   	inc    edx
  567fb8:	61                   	popa
  567fb9:	73 65                	jae    0x568020
  567fbb:	4d                   	dec    ebp
  567fbc:	65 73 68             	gs jae 0x568027
  567fbf:	9c                   	pushf
  567fc0:	1d 40 00 01 71       	sbb    eax,0x71010040
  567fc5:	57                   	push   edi
  567fc6:	83 2a 4d             	sub    DWORD PTR [edx],0x4d
  567fc9:	bf f4 43 8e 14       	mov    edi,0x148e43f4
  567fce:	82 a8 09 f1 7d 8a 05 	sub    BYTE PTR [eax-0x75820ef7],0x5
  567fd5:	64 33 64 78 39       	xor    esp,DWORD PTR fs:[eax+edi*2+0x39]
  567fda:	15 00 ff ff 02       	adc    eax,0x2ffff00
  567fdf:	00 e4                	add    ah,ah
  567fe1:	7f 56                	jg     0x568039
  567fe3:	00 0f                	add    BYTE PTR [edi],cl
  567fe5:	09 49 44             	or     DWORD PTR [ecx+0x44],ecx
  567fe8:	33 44 58 4d          	xor    eax,DWORD PTR [eax+ebx*2+0x4d]
  567fec:	65 73 68             	gs jae 0x568057
  567fef:	ac                   	lods   al,BYTE PTR ds:[esi]
  567ff0:	7f 56                	jg     0x568048
  567ff2:	00 01                	add    BYTE PTR [ecx],al
  567ff4:	3b 5c ae cc          	cmp    ebx,DWORD PTR [esi+ebp*4-0x34]
  567ff8:	d1 4d 0f             	ror    DWORD PTR [ebp+0xf],1
  567ffb:	4d                   	dec    ebp
  567ffc:	99                   	cdq
  567ffd:	7e 46                	jle    0x568045
  567fff:	84 ca                	test   dl,cl
  568001:	64 55                	fs push ebp
  568003:	7f 05                	jg     0x56800a
  568005:	64 33 64 78 39       	xor    esp,DWORD PTR fs:[eax+edi*2+0x39]
  56800a:	05 00 ff ff 02       	add    eax,0x2ffff00
  56800f:	00 ff                	add    bh,bh
  568011:	25 3c 48 86 00       	and    eax,0x86483c
  568016:	8b c0                	mov    eax,eax
  568018:	ff 25 38 48 86 00    	jmp    DWORD PTR ds:0x864838
  56801e:	8b c0                	mov    eax,eax
  568020:	ff 25 34 48 86 00    	jmp    DWORD PTR ds:0x864834
  568026:	8b c0                	mov    eax,eax
