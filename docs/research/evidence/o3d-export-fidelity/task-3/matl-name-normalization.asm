
/mnt/Random/users/user/Documents/Ghidra/OMSI/Omsi.exe:     file format pei-i386


Disassembly of section .text:

004213c4 <.text+0x203c4>:
  4213c4:	53                   	push   ebx
  4213c5:	56                   	push   esi
  4213c6:	57                   	push   edi
  4213c7:	8b fa                	mov    edi,edx
  4213c9:	8b d8                	mov    ebx,eax
  4213cb:	8b c3                	mov    eax,ebx
  4213cd:	85 c0                	test   eax,eax
  4213cf:	74 05                	je     0x4213d6
  4213d1:	83 e8 04             	sub    eax,0x4
  4213d4:	8b 00                	mov    eax,DWORD PTR [eax]
  4213d6:	8b f0                	mov    esi,eax
  4213d8:	8b c7                	mov    eax,edi
  4213da:	8b d6                	mov    edx,esi
  4213dc:	e8 cf 82 fe ff       	call   0x4096b0
  4213e1:	85 f6                	test   esi,esi
  4213e3:	7e 29                	jle    0x42140e
  4213e5:	8b 0f                	mov    ecx,DWORD PTR [edi]
  4213e7:	8b d6                	mov    edx,esi
  4213e9:	83 fa 01             	cmp    edx,0x1
  4213ec:	7c 20                	jl     0x42140e
  4213ee:	0f b7 03             	movzx  eax,WORD PTR [ebx]
  4213f1:	8b f0                	mov    esi,eax
  4213f3:	83 c6 bf             	add    esi,0xffffffbf
  4213f6:	66 83 ee 1a          	sub    si,0x1a
  4213fa:	73 04                	jae    0x421400
  4213fc:	66 83 c8 20          	or     ax,0x20
  421400:	66 89 01             	mov    WORD PTR [ecx],ax
  421403:	83 c1 02             	add    ecx,0x2
  421406:	83 c3 02             	add    ebx,0x2
  421409:	4a                   	dec    edx
  42140a:	85 d2                	test   edx,edx
  42140c:	75 e0                	jne    0x4213ee
  42140e:	5f                   	pop    edi
  42140f:	5e                   	pop    esi
  421410:	5b                   	pop    ebx
  421411:	c3                   	ret
