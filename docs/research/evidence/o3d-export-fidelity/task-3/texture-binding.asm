
/mnt/Random/users/user/Documents/Ghidra/OMSI/Omsi.exe:     file format pei-i386


Disassembly of section .text:

007fc500 <.text+0x3fb500>:
  7fc500:	55                   	push   ebp
  7fc501:	8b ec                	mov    ebp,esp
  7fc503:	81 c4 2c ff ff ff    	add    esp,0xffffff2c
  7fc509:	53                   	push   ebx
  7fc50a:	56                   	push   esi
  7fc50b:	57                   	push   edi
  7fc50c:	33 db                	xor    ebx,ebx
  7fc50e:	89 9d 2c ff ff ff    	mov    DWORD PTR [ebp-0xd4],ebx
  7fc514:	89 5d fc             	mov    DWORD PTR [ebp-0x4],ebx
  7fc517:	8b f2                	mov    esi,edx
  7fc519:	8d bd 40 ff ff ff    	lea    edi,[ebp-0xc0]
  7fc51f:	51                   	push   ecx
  7fc520:	b9 2f 00 00 00       	mov    ecx,0x2f
  7fc525:	f3 a5                	rep movs DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fc527:	59                   	pop    ecx
  7fc528:	89 8d 3c ff ff ff    	mov    DWORD PTR [ebp-0xc4],ecx
  7fc52e:	8d 85 40 ff ff ff    	lea    eax,[ebp-0xc0]
  7fc534:	8b 15 8c a5 7f 00    	mov    edx,DWORD PTR ds:0x7fa58c
  7fc53a:	e8 f1 d9 c0 ff       	call   0x409f30
  7fc53f:	33 c0                	xor    eax,eax
  7fc541:	55                   	push   ebp
  7fc542:	68 66 c8 7f 00       	push   0x7fc866
  7fc547:	64 ff 30             	push   DWORD PTR fs:[eax]
  7fc54a:	64 89 20             	mov    DWORD PTR fs:[eax],esp
  7fc54d:	b8 35 00 00 00       	mov    eax,0x35
  7fc552:	e8 21 97 00 00       	call   0x805c78
  7fc557:	84 c0                	test   al,al
  7fc559:	0f 84 cf 02 00 00    	je     0x7fc82e
  7fc55f:	8b 85 3c ff ff ff    	mov    eax,DWORD PTR [ebp-0xc4]
  7fc565:	89 85 38 ff ff ff    	mov    DWORD PTR [ebp-0xc8],eax
  7fc56b:	83 bd 3c ff ff ff 00 	cmp    DWORD PTR [ebp-0xc4],0x0
  7fc572:	0f 8d e9 00 00 00    	jge    0x7fc661
  7fc578:	8b 8d 3c ff ff ff    	mov    ecx,DWORD PTR [ebp-0xc4]
  7fc57e:	f7 d9                	neg    ecx
  7fc580:	71 05                	jno    0x7fc587
  7fc582:	e8 dd a3 c0 ff       	call   0x406964
  7fc587:	8b c1                	mov    eax,ecx
  7fc589:	bb e8 03 00 00       	mov    ebx,0x3e8
  7fc58e:	99                   	cdq
  7fc58f:	f7 fb                	idiv   ebx
  7fc591:	8b f0                	mov    esi,eax
  7fc593:	8b c1                	mov    eax,ecx
  7fc595:	b9 e8 03 00 00       	mov    ecx,0x3e8
  7fc59a:	99                   	cdq
  7fc59b:	f7 f9                	idiv   ecx
  7fc59d:	8b fa                	mov    edi,edx
  7fc59f:	83 fe 01             	cmp    esi,0x1
  7fc5a2:	75 53                	jne    0x7fc5f7
  7fc5a4:	a1 ac 98 85 00       	mov    eax,ds:0x8598ac
  7fc5a9:	83 38 00             	cmp    DWORD PTR [eax],0x0
  7fc5ac:	74 49                	je     0x7fc5f7
  7fc5ae:	85 ff                	test   edi,edi
  7fc5b0:	7c 45                	jl     0x7fc5f7
  7fc5b2:	a1 ac 98 85 00       	mov    eax,ds:0x8598ac
  7fc5b7:	8b 00                	mov    eax,DWORD PTR [eax]
  7fc5b9:	8b 00                	mov    eax,DWORD PTR [eax]
  7fc5bb:	e8 3c e2 c0 ff       	call   0x40a7fc
  7fc5c0:	3b f8                	cmp    edi,eax
  7fc5c2:	7d 33                	jge    0x7fc5f7
  7fc5c4:	a1 ac 98 85 00       	mov    eax,ds:0x8598ac
  7fc5c9:	8b 00                	mov    eax,DWORD PTR [eax]
  7fc5cb:	8b 00                	mov    eax,DWORD PTR [eax]
  7fc5cd:	85 c0                	test   eax,eax
  7fc5cf:	74 05                	je     0x7fc5d6
  7fc5d1:	3b 78 fc             	cmp    edi,DWORD PTR [eax-0x4]
  7fc5d4:	72 05                	jb     0x7fc5db
  7fc5d6:	e8 81 a3 c0 ff       	call   0x40695c
  7fc5db:	8d 14 7f             	lea    edx,[edi+edi*2]
  7fc5de:	8b 04 90             	mov    eax,DWORD PTR [eax+edx*4]
  7fc5e1:	50                   	push   eax
  7fc5e2:	0f b6 45 0c          	movzx  eax,BYTE PTR [ebp+0xc]
  7fc5e6:	50                   	push   eax
  7fc5e7:	a1 24 88 85 00       	mov    eax,ds:0x858824
  7fc5ec:	8b 00                	mov    eax,DWORD PTR [eax]
  7fc5ee:	50                   	push   eax
  7fc5ef:	8b 00                	mov    eax,DWORD PTR [eax]
  7fc5f1:	ff 90 04 01 00 00    	call   DWORD PTR [eax+0x104]
  7fc5f7:	83 fe 02             	cmp    esi,0x2
  7fc5fa:	0f 85 2e 02 00 00    	jne    0x7fc82e
  7fc600:	a1 38 8b 85 00       	mov    eax,ds:0x858b38
  7fc605:	83 38 00             	cmp    DWORD PTR [eax],0x0
  7fc608:	0f 84 20 02 00 00    	je     0x7fc82e
  7fc60e:	85 ff                	test   edi,edi
  7fc610:	0f 8c 18 02 00 00    	jl     0x7fc82e
  7fc616:	a1 38 8b 85 00       	mov    eax,ds:0x858b38
  7fc61b:	8b 00                	mov    eax,DWORD PTR [eax]
  7fc61d:	8b 00                	mov    eax,DWORD PTR [eax]
  7fc61f:	e8 d8 e1 c0 ff       	call   0x40a7fc
  7fc624:	3b f8                	cmp    edi,eax
  7fc626:	0f 8d 02 02 00 00    	jge    0x7fc82e
  7fc62c:	a1 38 8b 85 00       	mov    eax,ds:0x858b38
  7fc631:	8b 00                	mov    eax,DWORD PTR [eax]
  7fc633:	8b 00                	mov    eax,DWORD PTR [eax]
  7fc635:	85 c0                	test   eax,eax
  7fc637:	74 05                	je     0x7fc63e
  7fc639:	3b 78 fc             	cmp    edi,DWORD PTR [eax-0x4]
  7fc63c:	72 05                	jb     0x7fc643
  7fc63e:	e8 19 a3 c0 ff       	call   0x40695c
  7fc643:	8b 04 b8             	mov    eax,DWORD PTR [eax+edi*4]
  7fc646:	50                   	push   eax
  7fc647:	0f b6 45 0c          	movzx  eax,BYTE PTR [ebp+0xc]
  7fc64b:	50                   	push   eax
  7fc64c:	a1 24 88 85 00       	mov    eax,ds:0x858824
  7fc651:	8b 00                	mov    eax,DWORD PTR [eax]
  7fc653:	50                   	push   eax
  7fc654:	8b 00                	mov    eax,DWORD PTR [eax]
  7fc656:	ff 90 04 01 00 00    	call   DWORD PTR [eax+0x104]
  7fc65c:	e9 cd 01 00 00       	jmp    0x7fc82e
  7fc661:	a1 9c 98 85 00       	mov    eax,ds:0x85989c
  7fc666:	8b 00                	mov    eax,DWORD PTR [eax]
  7fc668:	8b 40 08             	mov    eax,DWORD PTR [eax+0x8]
  7fc66b:	e8 94 e1 c0 ff       	call   0x40a804
  7fc670:	3b 85 3c ff ff ff    	cmp    eax,DWORD PTR [ebp-0xc4]
  7fc676:	0f 8c b2 01 00 00    	jl     0x7fc82e
  7fc67c:	a1 0c 9d 85 00       	mov    eax,ds:0x859d0c
  7fc681:	83 38 00             	cmp    DWORD PTR [eax],0x0
  7fc684:	0f 84 d4 00 00 00    	je     0x7fc75e
  7fc68a:	a1 74 93 85 00       	mov    eax,ds:0x859374
  7fc68f:	83 38 00             	cmp    DWORD PTR [eax],0x0
  7fc692:	0f 84 c6 00 00 00    	je     0x7fc75e
  7fc698:	8b 45 f0             	mov    eax,DWORD PTR [ebp-0x10]
  7fc69b:	e8 64 e1 c0 ff       	call   0x40a804
  7fc6a0:	8b d8                	mov    ebx,eax
  7fc6a2:	85 db                	test   ebx,ebx
  7fc6a4:	0f 8c b4 00 00 00    	jl     0x7fc75e
  7fc6aa:	43                   	inc    ebx
  7fc6ab:	33 f6                	xor    esi,esi
  7fc6ad:	8b 45 f0             	mov    eax,DWORD PTR [ebp-0x10]
  7fc6b0:	85 c0                	test   eax,eax
  7fc6b2:	74 05                	je     0x7fc6b9
  7fc6b4:	3b 70 fc             	cmp    esi,DWORD PTR [eax-0x4]
  7fc6b7:	72 05                	jb     0x7fc6be
  7fc6b9:	e8 9e a2 c0 ff       	call   0x40695c
  7fc6be:	8b 04 b0             	mov    eax,DWORD PTR [eax+esi*4]
  7fc6c1:	8b 15 0c 9d 85 00    	mov    edx,DWORD PTR ds:0x859d0c
  7fc6c7:	8b 12                	mov    edx,DWORD PTR [edx]
  7fc6c9:	3b 42 08             	cmp    eax,DWORD PTR [edx+0x8]
  7fc6cc:	0f 8d 84 00 00 00    	jge    0x7fc756
  7fc6d2:	8b 45 f0             	mov    eax,DWORD PTR [ebp-0x10]
  7fc6d5:	85 c0                	test   eax,eax
  7fc6d7:	74 05                	je     0x7fc6de
  7fc6d9:	3b 70 fc             	cmp    esi,DWORD PTR [eax-0x4]
  7fc6dc:	72 05                	jb     0x7fc6e3
  7fc6de:	e8 79 a2 c0 ff       	call   0x40695c
  7fc6e3:	8b 04 b0             	mov    eax,DWORD PTR [eax+esi*4]
  7fc6e6:	8b 15 74 93 85 00    	mov    edx,DWORD PTR ds:0x859374
  7fc6ec:	8b 12                	mov    edx,DWORD PTR [edx]
  7fc6ee:	3b 42 0c             	cmp    eax,DWORD PTR [edx+0xc]
  7fc6f1:	7d 63                	jge    0x7fc756
  7fc6f3:	8b 45 f0             	mov    eax,DWORD PTR [ebp-0x10]
  7fc6f6:	85 c0                	test   eax,eax
  7fc6f8:	74 05                	je     0x7fc6ff
  7fc6fa:	3b 70 fc             	cmp    esi,DWORD PTR [eax-0x4]
  7fc6fd:	72 05                	jb     0x7fc704
  7fc6ff:	e8 58 a2 c0 ff       	call   0x40695c
  7fc704:	8b 14 b0             	mov    edx,DWORD PTR [eax+esi*4]
  7fc707:	8d 8d 30 ff ff ff    	lea    ecx,[ebp-0xd0]
  7fc70d:	a1 74 93 85 00       	mov    eax,ds:0x859374
  7fc712:	8b 00                	mov    eax,DWORD PTR [eax]
  7fc714:	e8 0b 9a e0 ff       	call   0x606124
  7fc719:	8b 85 30 ff ff ff    	mov    eax,DWORD PTR [ebp-0xd0]
  7fc71f:	3b 85 3c ff ff ff    	cmp    eax,DWORD PTR [ebp-0xc4]
  7fc725:	75 2f                	jne    0x7fc756
  7fc727:	8b 45 f0             	mov    eax,DWORD PTR [ebp-0x10]
  7fc72a:	85 c0                	test   eax,eax
  7fc72c:	74 05                	je     0x7fc733
  7fc72e:	3b 70 fc             	cmp    esi,DWORD PTR [eax-0x4]
  7fc731:	72 05                	jb     0x7fc738
  7fc733:	e8 24 a2 c0 ff       	call   0x40695c
  7fc738:	8b 14 b0             	mov    edx,DWORD PTR [eax+esi*4]
  7fc73b:	a1 0c 9d 85 00       	mov    eax,ds:0x859d0c
  7fc740:	8b 00                	mov    eax,DWORD PTR [eax]
  7fc742:	e8 29 c9 e0 ff       	call   0x609070
  7fc747:	8b 78 04             	mov    edi,DWORD PTR [eax+0x4]
  7fc74a:	85 ff                	test   edi,edi
  7fc74c:	7c 10                	jl     0x7fc75e
  7fc74e:	89 bd 38 ff ff ff    	mov    DWORD PTR [ebp-0xc8],edi
  7fc754:	eb 08                	jmp    0x7fc75e
  7fc756:	46                   	inc    esi
  7fc757:	4b                   	dec    ebx
  7fc758:	0f 85 4f ff ff ff    	jne    0x7fc6ad
  7fc75e:	83 7d 08 00          	cmp    DWORD PTR [ebp+0x8],0x0
  7fc762:	0f 84 92 00 00 00    	je     0x7fc7fa
  7fc768:	8b 5d 08             	mov    ebx,DWORD PTR [ebp+0x8]
  7fc76b:	8d 45 fc             	lea    eax,[ebp-0x4]
  7fc76e:	8b 13                	mov    edx,DWORD PTR [ebx]
  7fc770:	8b 0d 6c 1a 7c 00    	mov    ecx,DWORD PTR ds:0x7c1a6c
  7fc776:	e8 95 e3 c0 ff       	call   0x40ab10
  7fc77b:	8b 45 fc             	mov    eax,DWORD PTR [ebp-0x4]
  7fc77e:	e8 81 e0 c0 ff       	call   0x40a804
  7fc783:	8b d8                	mov    ebx,eax
  7fc785:	85 db                	test   ebx,ebx
  7fc787:	7c 71                	jl     0x7fc7fa
  7fc789:	43                   	inc    ebx
  7fc78a:	33 f6                	xor    esi,esi
  7fc78c:	8b 45 fc             	mov    eax,DWORD PTR [ebp-0x4]
  7fc78f:	85 c0                	test   eax,eax
  7fc791:	74 05                	je     0x7fc798
  7fc793:	3b 70 fc             	cmp    esi,DWORD PTR [eax-0x4]
  7fc796:	72 05                	jb     0x7fc79d
  7fc798:	e8 bf a1 c0 ff       	call   0x40695c
  7fc79d:	8b 04 b0             	mov    eax,DWORD PTR [eax+esi*4]
  7fc7a0:	8b 40 08             	mov    eax,DWORD PTR [eax+0x8]
  7fc7a3:	8b 40 04             	mov    eax,DWORD PTR [eax+0x4]
  7fc7a6:	8b 95 3c ff ff ff    	mov    edx,DWORD PTR [ebp-0xc4]
  7fc7ac:	8b 0d 9c 98 85 00    	mov    ecx,DWORD PTR ds:0x85989c
  7fc7b2:	8b 09                	mov    ecx,DWORD PTR [ecx]
  7fc7b4:	8b 49 08             	mov    ecx,DWORD PTR [ecx+0x8]
  7fc7b7:	85 c9                	test   ecx,ecx
  7fc7b9:	74 05                	je     0x7fc7c0
  7fc7bb:	3b 51 fc             	cmp    edx,DWORD PTR [ecx-0x4]
  7fc7be:	72 05                	jb     0x7fc7c5
  7fc7c0:	e8 97 a1 c0 ff       	call   0x40695c
  7fc7c5:	6b d2 0d             	imul   edx,edx,0xd
  7fc7c8:	8b 54 d1 24          	mov    edx,DWORD PTR [ecx+edx*8+0x24]
  7fc7cc:	e8 7f c9 c0 ff       	call   0x409150
  7fc7d1:	75 23                	jne    0x7fc7f6
  7fc7d3:	8b 45 fc             	mov    eax,DWORD PTR [ebp-0x4]
  7fc7d6:	85 c0                	test   eax,eax
  7fc7d8:	74 05                	je     0x7fc7df
  7fc7da:	3b 70 fc             	cmp    esi,DWORD PTR [eax-0x4]
  7fc7dd:	72 05                	jb     0x7fc7e4
  7fc7df:	e8 78 a1 c0 ff       	call   0x40695c
  7fc7e4:	8b 04 b0             	mov    eax,DWORD PTR [eax+esi*4]
  7fc7e7:	8b 78 04             	mov    edi,DWORD PTR [eax+0x4]
  7fc7ea:	85 ff                	test   edi,edi
  7fc7ec:	7c 0c                	jl     0x7fc7fa
  7fc7ee:	89 bd 38 ff ff ff    	mov    DWORD PTR [ebp-0xc8],edi
  7fc7f4:	eb 04                	jmp    0x7fc7fa
  7fc7f6:	46                   	inc    esi
  7fc7f7:	4b                   	dec    ebx
  7fc7f8:	75 92                	jne    0x7fc78c
  7fc7fa:	8d 8d 2c ff ff ff    	lea    ecx,[ebp-0xd4]
  7fc800:	a1 9c 98 85 00       	mov    eax,ds:0x85989c
  7fc805:	8b 00                	mov    eax,DWORD PTR [eax]
  7fc807:	8b 95 38 ff ff ff    	mov    edx,DWORD PTR [ebp-0xc8]
  7fc80d:	e8 e6 cb ff ff       	call   0x7f93f8
  7fc812:	8b 85 2c ff ff ff    	mov    eax,DWORD PTR [ebp-0xd4]
  7fc818:	50                   	push   eax
  7fc819:	0f b6 45 0c          	movzx  eax,BYTE PTR [ebp+0xc]
  7fc81d:	50                   	push   eax
  7fc81e:	a1 24 88 85 00       	mov    eax,ds:0x858824
  7fc823:	8b 00                	mov    eax,DWORD PTR [eax]
  7fc825:	50                   	push   eax
  7fc826:	8b 00                	mov    eax,DWORD PTR [eax]
  7fc828:	ff 90 04 01 00 00    	call   DWORD PTR [eax+0x104]
  7fc82e:	33 c0                	xor    eax,eax
  7fc830:	5a                   	pop    edx
  7fc831:	59                   	pop    ecx
  7fc832:	59                   	pop    ecx
  7fc833:	64 89 10             	mov    DWORD PTR fs:[eax],edx
  7fc836:	68 6d c8 7f 00       	push   0x7fc86d
  7fc83b:	8d 85 2c ff ff ff    	lea    eax,[ebp-0xd4]
  7fc841:	e8 0a f8 c0 ff       	call   0x40c050
  7fc846:	8d 85 40 ff ff ff    	lea    eax,[ebp-0xc0]
  7fc84c:	8b 15 8c a5 7f 00    	mov    edx,DWORD PTR ds:0x7fa58c
  7fc852:	e8 6d d5 c0 ff       	call   0x409dc4
  7fc857:	8d 45 fc             	lea    eax,[ebp-0x4]
  7fc85a:	8b 15 6c 1a 7c 00    	mov    edx,DWORD PTR ds:0x7c1a6c
  7fc860:	e8 6f e2 c0 ff       	call   0x40aad4
  7fc865:	c3                   	ret
  7fc866:	e9 41 b5 c0 ff       	jmp    0x407dac
  7fc86b:	eb ce                	jmp    0x7fc83b
  7fc86d:	5f                   	pop    edi
  7fc86e:	5e                   	pop    esi
  7fc86f:	5b                   	pop    ebx
  7fc870:	8b e5                	mov    esp,ebp
  7fc872:	5d                   	pop    ebp
  7fc873:	c2 08 00             	ret    0x8
  7fc876:	8b c0                	mov    eax,eax
