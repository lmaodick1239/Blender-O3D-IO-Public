
/mnt/Random/users/user/Documents/Ghidra/OMSI/Omsi.exe:     file format pei-i386


Disassembly of section .text:

00561748 <.text+0x160748>:
  561748:	05 00 01 00 00       	add    eax,0x100
  56174d:	73 05                	jae    0x561754
  56174f:	e8 10 52 ea ff       	call   0x406964
  561754:	c3                   	ret
  561755:	8d 40 00             	lea    eax,[eax+0x0]
  561758:	ff 25 f0 47 86 00    	jmp    DWORD PTR ds:0x8647f0
  56175e:	8b c0                	mov    eax,eax
  561760:	55                   	push   ebp
  561761:	8b ec                	mov    ebp,esp
  561763:	53                   	push   ebx
  561764:	56                   	push   esi
  561765:	8b da                	mov    ebx,edx
  561767:	8b f0                	mov    esi,eax
  561769:	56                   	push   esi
  56176a:	e8 e9 ff ff ff       	call   0x561758
  56176f:	8b d0                	mov    edx,eax
  561771:	8b c3                	mov    eax,ebx
  561773:	e8 f0 a8 ea ff       	call   0x40c068
  561778:	83 3b 00             	cmp    DWORD PTR [ebx],0x0
  56177b:	74 08                	je     0x561785
  56177d:	8b 03                	mov    eax,DWORD PTR [ebx]
  56177f:	50                   	push   eax
  561780:	8b 00                	mov    eax,DWORD PTR [eax]
  561782:	ff 50 08             	call   DWORD PTR [eax+0x8]
  561785:	5e                   	pop    esi
  561786:	5b                   	pop    ebx
  561787:	5d                   	pop    ebp
  561788:	c3                   	ret
  561789:	8d 40 00             	lea    eax,[eax+0x0]
  56178c:	90                   	nop
  56178d:	17                   	pop    ss
  56178e:	56                   	push   esi
	...
