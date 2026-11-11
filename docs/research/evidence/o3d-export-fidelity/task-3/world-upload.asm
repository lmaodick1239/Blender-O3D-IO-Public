// Bounded evidence excerpt; not compilable source. Original: docs/research/evidence/o3d-export-fidelity/native-geometry/mesh-setup.asm
// Original SHA256 cde361314869e5f9622da691db5b294f237ddcd2782ad9c052afbf5599c59869; original bytes 17173
// Source line ranges (inclusive): [(200, 281)]

// BEGIN original lines 200..281
  7c3194:	55                   	push   ebp
  7c3195:	8b ec                	mov    ebp,esp
  7c3197:	53                   	push   ebx
  7c3198:	56                   	push   esi
  7c3199:	8b d8                	mov    ebx,eax
  7c319b:	8b c3                	mov    eax,ebx
  7c319d:	e8 0e fe ff ff       	call   0x7c2fb0
  7c31a2:	8b c3                	mov    eax,ebx
  7c31a4:	e8 07 00 00 00       	call   0x7c31b0
  7c31a9:	8b c6                	mov    eax,esi
  7c31ab:	5e                   	pop    esi
  7c31ac:	5b                   	pop    ebx
  7c31ad:	5d                   	pop    ebp
  7c31ae:	c3                   	ret
  7c31af:	90                   	nop
  7c31b0:	55                   	push   ebp
  7c31b1:	8b ec                	mov    ebp,esp
  7c31b3:	83 c4 c0             	add    esp,0xffffffc0
  7c31b6:	53                   	push   ebx
  7c31b7:	8b d8                	mov    ebx,eax
  7c31b9:	a1 08 9e 85 00       	mov    eax,ds:0x859e08
  7c31be:	80 38 00             	cmp    BYTE PTR [eax],0x0
  7c31c1:	0f 84 86 00 00 00    	je     0x7c324d
  7c31c7:	8d 43 20             	lea    eax,[ebx+0x20]
  7c31ca:	50                   	push   eax
  7c31cb:	68 70 32 7c 00       	push   0x7c3270
  7c31d0:	a1 08 95 85 00       	mov    eax,ds:0x859508
  7c31d5:	8b 00                	mov    eax,DWORD PTR [eax]
  7c31d7:	50                   	push   eax
  7c31d8:	8b 00                	mov    eax,DWORD PTR [eax]
  7c31da:	ff 90 98 00 00 00    	call   DWORD PTR [eax+0x98]
  7c31e0:	b1 03                	mov    cl,0x3
  7c31e2:	ba 84 32 7c 00       	mov    edx,0x7c3284
  7c31e7:	e8 c0 f7 03 00       	call   0x8029ac
  7c31ec:	a1 20 9d 85 00       	mov    eax,ds:0x859d20
  7c31f1:	50                   	push   eax
  7c31f2:	8d 43 20             	lea    eax,[ebx+0x20]
  7c31f5:	50                   	push   eax
  7c31f6:	8d 45 c0             	lea    eax,[ebp-0x40]
  7c31f9:	50                   	push   eax
  7c31fa:	e8 91 4c da ff       	call   0x567e90
  7c31ff:	8d 45 c0             	lea    eax,[ebp-0x40]
  7c3202:	50                   	push   eax
  7c3203:	68 9c 32 7c 00       	push   0x7c329c
  7c3208:	a1 08 95 85 00       	mov    eax,ds:0x859508
  7c320d:	8b 00                	mov    eax,DWORD PTR [eax]
  7c320f:	50                   	push   eax
  7c3210:	8b 00                	mov    eax,DWORD PTR [eax]
  7c3212:	ff 90 98 00 00 00    	call   DWORD PTR [eax+0x98]
  7c3218:	b1 03                	mov    cl,0x3
  7c321a:	ba b4 32 7c 00       	mov    edx,0x7c32b4
  7c321f:	e8 88 f7 03 00       	call   0x8029ac
  7c3224:	a1 e8 97 85 00       	mov    eax,ds:0x8597e8
  7c3229:	50                   	push   eax
  7c322a:	68 d4 32 7c 00       	push   0x7c32d4
  7c322f:	a1 08 95 85 00       	mov    eax,ds:0x859508
  7c3234:	8b 00                	mov    eax,DWORD PTR [eax]
  7c3236:	50                   	push   eax
  7c3237:	8b 00                	mov    eax,DWORD PTR [eax]
  7c3239:	ff 90 98 00 00 00    	call   DWORD PTR [eax+0x98]
  7c323f:	b1 03                	mov    cl,0x3
  7c3241:	ba ec 32 7c 00       	mov    edx,0x7c32ec
  7c3246:	e8 61 f7 03 00       	call   0x8029ac
  7c324b:	eb 1c                	jmp    0x7c3269
  7c324d:	8d 43 20             	lea    eax,[ebx+0x20]
  7c3250:	50                   	push   eax
  7c3251:	33 c0                	xor    eax,eax
  7c3253:	e8 f0 e4 d9 ff       	call   0x561748
  7c3258:	50                   	push   eax
  7c3259:	a1 24 88 85 00       	mov    eax,ds:0x858824
  7c325e:	8b 00                	mov    eax,DWORD PTR [eax]
  7c3260:	50                   	push   eax
  7c3261:	8b 00                	mov    eax,DWORD PTR [eax]
  7c3263:	ff 90 b0 00 00 00    	call   DWORD PTR [eax+0xb0]
  7c3269:	5b                   	pop    ebx
  7c326a:	8b e5                	mov    esp,ebp
  7c326c:	5d                   	pop    ebp
  7c326d:	c3                   	ret
  7c326e:	00 00                	add    BYTE PTR [eax],al
  7c3270:	67 4d                	addr16 dec ebp
  7c3272:	61                   	popa
  7c3273:	74 4f                	je     0x7c32c4
// END original lines 200..281
