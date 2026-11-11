// Bounded original-PE excerpt; original docs/research/evidence/o3d-export-fidelity/native-geometry/mesh-load-wrapper.asm
// Original SHA256 a3debc0d5ba816602baee07b2d537537d0177c6a2900d8db86a685742f2a6ef4; original bytes 12287; original lines 133..162
  7c70b2:	8d 55 e0             	lea    edx,[ebp-0x20]
  7c70b5:	8b 45 f0             	mov    eax,DWORD PTR [ebp-0x10]
  7c70b8:	8b 80 7c 01 00 00    	mov    eax,DWORD PTR [eax+0x17c]
  7c70be:	e8 f1 56 da ff       	call   0x56c7b4
  7c70c3:	84 c0                	test   al,al
  7c70c5:	75 3a                	jne    0x7c7101
  7c70c7:	68 78 73 7c 00       	push   0x7c7378
  7c70cc:	8b 45 f0             	mov    eax,DWORD PTR [ebp-0x10]
  7c70cf:	ff b0 7c 01 00 00    	push   DWORD PTR [eax+0x17c]
  7c70d5:	68 8c 73 7c 00       	push   0x7c738c
  7c70da:	8d 45 ac             	lea    eax,[ebp-0x54]
  7c70dd:	ba 03 00 00 00       	mov    edx,0x3
  7c70e2:	e8 a1 1f c4 ff       	call   0x409088
  7c70e7:	8b 55 ac             	mov    edx,DWORD PTR [ebp-0x54]
  7c70ea:	8d 45 b0             	lea    eax,[ebp-0x50]
  7c70ed:	e8 02 25 c4 ff       	call   0x4095f4
  7c70f2:	8b 45 b0             	mov    eax,DWORD PTR [ebp-0x50]
  7c70f5:	b2 02                	mov    dl,0x2
  7c70f7:	e8 c4 b1 03 00       	call   0x8022c0
  7c70fc:	e9 92 01 00 00       	jmp    0x7c7293
  7c7101:	8b 45 08             	mov    eax,DWORD PTR [ebp+0x8]
  7c7104:	50                   	push   eax
  7c7105:	8d 45 a8             	lea    eax,[ebp-0x58]
  7c7108:	8b 55 f8             	mov    edx,DWORD PTR [ebp-0x8]
  7c710b:	b9 00 00 00 00       	mov    ecx,0x0
  7c7110:	e8 b7 21 c4 ff       	call   0x4092cc
  7c7115:	8b 4d a8             	mov    ecx,DWORD PTR [ebp-0x58]
  7c7118:	8b 55 e0             	mov    edx,DWORD PTR [ebp-0x20]
  7c711b:	8b 45 f0             	mov    eax,DWORD PTR [ebp-0x10]
  7c711e:	e8 29 e9 ff ff       	call   0x7c5a4c
