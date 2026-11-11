// Bounded evidence excerpt; not compilable source. Original: docs/research/evidence/o3d-export-fidelity/native-geometry/instance-animation-consumers.asm
// Original SHA256 a1aba0c87368dc27b431d571a86c3a8f52f8061d4a343f84ba07417bb89933da; original bytes 143958
// Source line ranges (inclusive): [(1171, 1272), (2420, 2468)]

// BEGIN original lines 1171..1272
  5fc538:	55                   	push   ebp
  5fc539:	8b ec                	mov    ebp,esp
  5fc53b:	83 c4 bc             	add    esp,0xffffffbc
  5fc53e:	53                   	push   ebx
  5fc53f:	56                   	push   esi
  5fc540:	57                   	push   edi
  5fc541:	8b f2                	mov    esi,edx
  5fc543:	8d 7d bc             	lea    edi,[ebp-0x44]
  5fc546:	b9 10 00 00 00       	mov    ecx,0x10
  5fc54b:	f3 a5                	rep movs DWORD PTR es:[edi],DWORD PTR ds:[esi]
  5fc54d:	8b d8                	mov    ebx,eax
  5fc54f:	80 bb f0 00 00 00 00 	cmp    BYTE PTR [ebx+0xf0],0x0
  5fc556:	0f 85 ff 00 00 00    	jne    0x5fc65b
  5fc55c:	8d 75 bc             	lea    esi,[ebp-0x44]
  5fc55f:	8d 7b 5c             	lea    edi,[ebx+0x5c]
  5fc562:	b9 10 00 00 00       	mov    ecx,0x10
  5fc567:	f3 a5                	rep movs DWORD PTR es:[edi],DWORD PTR ds:[esi]
  5fc569:	8b 43 20             	mov    eax,DWORD PTR [ebx+0x20]
  5fc56c:	8b 40 38             	mov    eax,DWORD PTR [eax+0x38]
  5fc56f:	8b 40 08             	mov    eax,DWORD PTR [eax+0x8]
  5fc572:	83 e8 01             	sub    eax,0x1
  5fc575:	71 05                	jno    0x5fc57c
  5fc577:	e8 e8 a3 e0 ff       	call   0x406964
  5fc57c:	85 c0                	test   eax,eax
  5fc57e:	0f 8c d0 00 00 00    	jl     0x5fc654
  5fc584:	40                   	inc    eax
  5fc585:	89 45 fc             	mov    DWORD PTR [ebp-0x4],eax
  5fc588:	33 f6                	xor    esi,esi
  5fc58a:	8b d6                	mov    edx,esi
  5fc58c:	8b 83 e0 00 00 00    	mov    eax,DWORD PTR [ebx+0xe0]
  5fc592:	e8 61 e9 00 00       	call   0x60aef8
  5fc597:	8b f8                	mov    edi,eax
  5fc599:	a1 54 99 85 00       	mov    eax,ds:0x859954
  5fc59e:	56                   	push   esi
  5fc59f:	57                   	push   edi
  5fc5a0:	8b f0                	mov    esi,eax
  5fc5a2:	81 c7 88 00 00 00    	add    edi,0x88
  5fc5a8:	b9 10 00 00 00       	mov    ecx,0x10
  5fc5ad:	f3 a5                	rep movs DWORD PTR es:[edi],DWORD PTR ds:[esi]
  5fc5af:	5f                   	pop    edi
  5fc5b0:	5e                   	pop    esi
  5fc5b1:	56                   	push   esi
  5fc5b2:	57                   	push   edi
  5fc5b3:	83 c7 08             	add    edi,0x8
  5fc5b6:	8d 75 bc             	lea    esi,[ebp-0x44]
  5fc5b9:	b9 10 00 00 00       	mov    ecx,0x10
  5fc5be:	f3 a5                	rep movs DWORD PTR es:[edi],DWORD PTR ds:[esi]
  5fc5c0:	5f                   	pop    edi
  5fc5c1:	5e                   	pop    esi
  5fc5c2:	8b 43 20             	mov    eax,DWORD PTR [ebx+0x20]
  5fc5c5:	8b 40 38             	mov    eax,DWORD PTR [eax+0x38]
  5fc5c8:	8b d6                	mov    edx,esi
  5fc5ca:	e8 5d 72 00 00       	call   0x60382c
  5fc5cf:	80 b8 f4 00 00 00 00 	cmp    BYTE PTR [eax+0xf4],0x0
  5fc5d6:	74 3c                	je     0x5fc614
  5fc5d8:	8b d6                	mov    edx,esi
  5fc5da:	8b 83 e0 00 00 00    	mov    eax,DWORD PTR [ebx+0xe0]
  5fc5e0:	e8 13 e9 00 00       	call   0x60aef8
  5fc5e5:	83 c0 08             	add    eax,0x8
  5fc5e8:	50                   	push   eax
  5fc5e9:	8b 43 20             	mov    eax,DWORD PTR [ebx+0x20]
  5fc5ec:	8b 40 38             	mov    eax,DWORD PTR [eax+0x38]
  5fc5ef:	8b d6                	mov    edx,esi
  5fc5f1:	e8 36 72 00 00       	call   0x60382c
  5fc5f6:	05 35 01 00 00       	add    eax,0x135
  5fc5fb:	50                   	push   eax
  5fc5fc:	8b d6                	mov    edx,esi
  5fc5fe:	8b 83 e0 00 00 00    	mov    eax,DWORD PTR [ebx+0xe0]
  5fc604:	e8 ef e8 00 00       	call   0x60aef8
  5fc609:	83 c0 48             	add    eax,0x48
  5fc60c:	50                   	push   eax
  5fc60d:	e8 7e b8 f6 ff       	call   0x567e90
  5fc612:	eb 2f                	jmp    0x5fc643
  5fc614:	8b d6                	mov    edx,esi
  5fc616:	8b 83 e0 00 00 00    	mov    eax,DWORD PTR [ebx+0xe0]
  5fc61c:	e8 d7 e8 00 00       	call   0x60aef8
  5fc621:	83 c0 08             	add    eax,0x8
  5fc624:	50                   	push   eax
  5fc625:	8b d6                	mov    edx,esi
  5fc627:	8b 83 e0 00 00 00    	mov    eax,DWORD PTR [ebx+0xe0]
  5fc62d:	e8 c6 e8 00 00       	call   0x60aef8
  5fc632:	5a                   	pop    edx
  5fc633:	56                   	push   esi
  5fc634:	57                   	push   edi
  5fc635:	8b f2                	mov    esi,edx
  5fc637:	8d 78 48             	lea    edi,[eax+0x48]
  5fc63a:	b9 10 00 00 00       	mov    ecx,0x10
  5fc63f:	f3 a5                	rep movs DWORD PTR es:[edi],DWORD PTR ds:[esi]
  5fc641:	5f                   	pop    edi
  5fc642:	5e                   	pop    esi
  5fc643:	c6 87 d0 00 00 00 01 	mov    BYTE PTR [edi+0xd0],0x1
  5fc64a:	46                   	inc    esi
  5fc64b:	ff 4d fc             	dec    DWORD PTR [ebp-0x4]
  5fc64e:	0f 85 36 ff ff ff    	jne    0x5fc58a
  5fc654:	c6 83 f0 00 00 00 01 	mov    BYTE PTR [ebx+0xf0],0x1
  5fc65b:	5f                   	pop    edi
  5fc65c:	5e                   	pop    esi
  5fc65d:	5b                   	pop    ebx
  5fc65e:	8b e5                	mov    esp,ebp
  5fc660:	5d                   	pop    ebp
  5fc661:	c3                   	ret
  5fc662:	8b c0                	mov    eax,eax
// END original lines 1171..1272

// BEGIN original lines 2420..2468
  5fd600:	55                   	push   ebp
  5fd601:	8b ec                	mov    ebp,esp
  5fd603:	53                   	push   ebx
  5fd604:	56                   	push   esi
  5fd605:	57                   	push   edi
  5fd606:	8b f0                	mov    esi,eax
  5fd608:	8b 46 20             	mov    eax,DWORD PTR [esi+0x20]
  5fd60b:	8b 40 38             	mov    eax,DWORD PTR [eax+0x38]
  5fd60e:	8b 78 08             	mov    edi,DWORD PTR [eax+0x8]
  5fd611:	83 ef 01             	sub    edi,0x1
  5fd614:	71 05                	jno    0x5fd61b
  5fd616:	e8 49 93 e0 ff       	call   0x406964
  5fd61b:	85 ff                	test   edi,edi
  5fd61d:	7c 2b                	jl     0x5fd64a
  5fd61f:	47                   	inc    edi
  5fd620:	33 db                	xor    ebx,ebx
  5fd622:	8b d3                	mov    edx,ebx
  5fd624:	8b 86 e0 00 00 00    	mov    eax,DWORD PTR [esi+0xe0]
  5fd62a:	e8 c9 d8 00 00       	call   0x60aef8
  5fd62f:	83 c0 48             	add    eax,0x48
  5fd632:	50                   	push   eax
  5fd633:	8b 46 20             	mov    eax,DWORD PTR [esi+0x20]
  5fd636:	8b 40 38             	mov    eax,DWORD PTR [eax+0x38]
  5fd639:	8b d3                	mov    edx,ebx
  5fd63b:	e8 ec 61 00 00       	call   0x60382c
  5fd640:	5a                   	pop    edx
  5fd641:	e8 16 5b 1c 00       	call   0x7c315c
  5fd646:	43                   	inc    ebx
  5fd647:	4f                   	dec    edi
  5fd648:	75 d8                	jne    0x5fd622
  5fd64a:	5f                   	pop    edi
  5fd64b:	5e                   	pop    esi
  5fd64c:	5b                   	pop    ebx
  5fd64d:	5d                   	pop    ebp
  5fd64e:	c3                   	ret
  5fd64f:	90                   	nop
  5fd650:	55                   	push   ebp
  5fd651:	8b ec                	mov    ebp,esp
  5fd653:	83 c4 ec             	add    esp,0xffffffec
  5fd656:	53                   	push   ebx
  5fd657:	56                   	push   esi
  5fd658:	57                   	push   edi
  5fd659:	8b d8                	mov    ebx,eax
  5fd65b:	8b 43 20             	mov    eax,DWORD PTR [ebx+0x20]
  5fd65e:	8b 40 40             	mov    eax,DWORD PTR [eax+0x40]
  5fd661:	8b 78 08             	mov    edi,DWORD PTR [eax+0x8]
  5fd664:	83 ef 01             	sub    edi,0x1
  5fd667:	71 05                	jno    0x5fd66e
  5fd669:	e8 f6 92 e0 ff       	call   0x406964
// END original lines 2420..2468
