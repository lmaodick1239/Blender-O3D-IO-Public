
/mnt/Random/users/user/Documents/Ghidra/OMSI/Omsi.exe:     file format pei-i386


Disassembly of section .text:

007fb22c <.text+0x3fa22c>:
  7fb22c:	55                   	push   ebp
  7fb22d:	8b ec                	mov    ebp,esp
  7fb22f:	83 c4 f0             	add    esp,0xfffffff0
  7fb232:	53                   	push   ebx
  7fb233:	56                   	push   esi
  7fb234:	57                   	push   edi
  7fb235:	84 d2                	test   dl,dl
  7fb237:	74 08                	je     0x7fb241
  7fb239:	83 c4 f0             	add    esp,0xfffffff0
  7fb23c:	e8 d7 be c0 ff       	call   0x407118
  7fb241:	8b da                	mov    ebx,edx
  7fb243:	8b f8                	mov    edi,eax
  7fb245:	be e8 1b 86 00       	mov    esi,0x861be8
  7fb24a:	8b c7                	mov    eax,edi
  7fb24c:	e8 5b 5a 00 00       	call   0x800cac
  7fb251:	6a 00                	push   0x0
  7fb253:	8d 47 04             	lea    eax,[edi+0x4]
  7fb256:	b9 01 00 00 00       	mov    ecx,0x1
  7fb25b:	8b 15 74 aa 7f 00    	mov    edx,DWORD PTR ds:0x7faa74
  7fb261:	e8 4a f7 c0 ff       	call   0x40a9b0
  7fb266:	83 c4 04             	add    esp,0x4
  7fb269:	68 00 00 80 3f       	push   0x3f800000
  7fb26e:	68 00 00 80 3f       	push   0x3f800000
  7fb273:	68 00 00 80 3f       	push   0x3f800000
  7fb278:	68 00 00 80 3f       	push   0x3f800000
  7fb27d:	8d 45 f0             	lea    eax,[ebp-0x10]
  7fb280:	e8 d7 8a ff ff       	call   0x7f3d5c
  7fb285:	56                   	push   esi
  7fb286:	57                   	push   edi
  7fb287:	8d 75 f0             	lea    esi,[ebp-0x10]
  7fb28a:	83 c7 08             	add    edi,0x8
  7fb28d:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb28e:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb28f:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb290:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb291:	5f                   	pop    edi
  7fb292:	5e                   	pop    esi
  7fb293:	68 00 00 80 3f       	push   0x3f800000
  7fb298:	68 00 00 80 3f       	push   0x3f800000
  7fb29d:	68 00 00 80 3f       	push   0x3f800000
  7fb2a2:	68 00 00 80 3f       	push   0x3f800000
  7fb2a7:	8d 45 f0             	lea    eax,[ebp-0x10]
  7fb2aa:	e8 ad 8a ff ff       	call   0x7f3d5c
  7fb2af:	56                   	push   esi
  7fb2b0:	57                   	push   edi
  7fb2b1:	8d 75 f0             	lea    esi,[ebp-0x10]
  7fb2b4:	83 c7 18             	add    edi,0x18
  7fb2b7:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb2b8:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb2b9:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb2ba:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb2bb:	5f                   	pop    edi
  7fb2bc:	5e                   	pop    esi
  7fb2bd:	6a 00                	push   0x0
  7fb2bf:	6a 00                	push   0x0
  7fb2c1:	6a 00                	push   0x0
  7fb2c3:	6a 00                	push   0x0
  7fb2c5:	8d 45 f0             	lea    eax,[ebp-0x10]
  7fb2c8:	e8 8f 8a ff ff       	call   0x7f3d5c
  7fb2cd:	56                   	push   esi
  7fb2ce:	57                   	push   edi
  7fb2cf:	8d 75 f0             	lea    esi,[ebp-0x10]
  7fb2d2:	83 c7 28             	add    edi,0x28
  7fb2d5:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb2d6:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb2d7:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb2d8:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb2d9:	5f                   	pop    edi
  7fb2da:	5e                   	pop    esi
  7fb2db:	6a 00                	push   0x0
  7fb2dd:	6a 00                	push   0x0
  7fb2df:	6a 00                	push   0x0
  7fb2e1:	6a 00                	push   0x0
  7fb2e3:	8d 45 f0             	lea    eax,[ebp-0x10]
  7fb2e6:	e8 71 8a ff ff       	call   0x7f3d5c
  7fb2eb:	56                   	push   esi
  7fb2ec:	57                   	push   edi
  7fb2ed:	8d 75 f0             	lea    esi,[ebp-0x10]
  7fb2f0:	83 c7 38             	add    edi,0x38
  7fb2f3:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb2f4:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb2f5:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb2f6:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb2f7:	5f                   	pop    edi
  7fb2f8:	5e                   	pop    esi
  7fb2f9:	33 c0                	xor    eax,eax
  7fb2fb:	89 47 48             	mov    DWORD PTR [edi+0x48],eax
  7fb2fe:	6a 00                	push   0x0
  7fb300:	6a 00                	push   0x0
  7fb302:	6a 00                	push   0x0
  7fb304:	6a 00                	push   0x0
  7fb306:	8d 45 f0             	lea    eax,[ebp-0x10]
  7fb309:	e8 4e 8a ff ff       	call   0x7f3d5c
  7fb30e:	56                   	push   esi
  7fb30f:	57                   	push   edi
  7fb310:	8d 75 f0             	lea    esi,[ebp-0x10]
  7fb313:	83 c7 4c             	add    edi,0x4c
  7fb316:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb317:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb318:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb319:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb31a:	5f                   	pop    edi
  7fb31b:	5e                   	pop    esi
  7fb31c:	6a 00                	push   0x0
  7fb31e:	6a 00                	push   0x0
  7fb320:	6a 00                	push   0x0
  7fb322:	6a 00                	push   0x0
  7fb324:	8d 45 f0             	lea    eax,[ebp-0x10]
  7fb327:	e8 30 8a ff ff       	call   0x7f3d5c
  7fb32c:	56                   	push   esi
  7fb32d:	57                   	push   edi
  7fb32e:	8d 75 f0             	lea    esi,[ebp-0x10]
  7fb331:	83 c7 5c             	add    edi,0x5c
  7fb334:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb335:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb336:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb337:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb338:	5f                   	pop    edi
  7fb339:	5e                   	pop    esi
  7fb33a:	6a 00                	push   0x0
  7fb33c:	6a 00                	push   0x0
  7fb33e:	6a 00                	push   0x0
  7fb340:	6a 00                	push   0x0
  7fb342:	8d 45 f0             	lea    eax,[ebp-0x10]
  7fb345:	e8 12 8a ff ff       	call   0x7f3d5c
  7fb34a:	56                   	push   esi
  7fb34b:	57                   	push   edi
  7fb34c:	8d 75 f0             	lea    esi,[ebp-0x10]
  7fb34f:	83 c7 6c             	add    edi,0x6c
  7fb352:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb353:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb354:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb355:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb356:	5f                   	pop    edi
  7fb357:	5e                   	pop    esi
  7fb358:	68 66 66 66 3f       	push   0x3f666666
  7fb35d:	68 66 66 66 3f       	push   0x3f666666
  7fb362:	68 66 66 66 3f       	push   0x3f666666
  7fb367:	68 66 66 66 3f       	push   0x3f666666
  7fb36c:	8d 45 f0             	lea    eax,[ebp-0x10]
  7fb36f:	e8 e8 89 ff ff       	call   0x7f3d5c
  7fb374:	56                   	push   esi
  7fb375:	57                   	push   edi
  7fb376:	8d 75 f0             	lea    esi,[ebp-0x10]
  7fb379:	83 c7 7c             	add    edi,0x7c
  7fb37c:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb37d:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb37e:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb37f:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb380:	5f                   	pop    edi
  7fb381:	5e                   	pop    esi
  7fb382:	33 c0                	xor    eax,eax
  7fb384:	89 87 8c 00 00 00    	mov    DWORD PTR [edi+0x8c],eax
  7fb38a:	c7 06 ff ff ff ff    	mov    DWORD PTR [esi],0xffffffff
  7fb390:	c7 46 18 ff ff ff ff 	mov    DWORD PTR [esi+0x18],0xffffffff
  7fb397:	c7 46 1c ff ff ff ff 	mov    DWORD PTR [esi+0x1c],0xffffffff
  7fb39e:	c6 46 5c 00          	mov    BYTE PTR [esi+0x5c],0x0
  7fb3a2:	6a 00                	push   0x0
  7fb3a4:	8d 46 40             	lea    eax,[esi+0x40]
  7fb3a7:	b9 01 00 00 00       	mov    ecx,0x1
  7fb3ac:	8b 15 1c a5 7f 00    	mov    edx,DWORD PTR ds:0x7fa51c
  7fb3b2:	e8 f9 f5 c0 ff       	call   0x40a9b0
  7fb3b7:	83 c4 04             	add    esp,0x4
  7fb3ba:	6a 00                	push   0x0
  7fb3bc:	6a 00                	push   0x0
  7fb3be:	6a 00                	push   0x0
  7fb3c0:	6a 00                	push   0x0
  7fb3c2:	8d 45 f0             	lea    eax,[ebp-0x10]
  7fb3c5:	e8 92 89 ff ff       	call   0x7f3d5c
  7fb3ca:	56                   	push   esi
  7fb3cb:	57                   	push   edi
  7fb3cc:	8d 7e 6c             	lea    edi,[esi+0x6c]
  7fb3cf:	8d 75 f0             	lea    esi,[ebp-0x10]
  7fb3d2:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb3d3:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb3d4:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb3d5:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb3d6:	5f                   	pop    edi
  7fb3d7:	5e                   	pop    esi
  7fb3d8:	6a 00                	push   0x0
  7fb3da:	6a 00                	push   0x0
  7fb3dc:	6a 00                	push   0x0
  7fb3de:	6a 00                	push   0x0
  7fb3e0:	8d 45 f0             	lea    eax,[ebp-0x10]
  7fb3e3:	e8 74 89 ff ff       	call   0x7f3d5c
  7fb3e8:	56                   	push   esi
  7fb3e9:	57                   	push   edi
  7fb3ea:	8d 7e 7c             	lea    edi,[esi+0x7c]
  7fb3ed:	8d 75 f0             	lea    esi,[ebp-0x10]
  7fb3f0:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb3f1:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb3f2:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb3f3:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb3f4:	5f                   	pop    edi
  7fb3f5:	5e                   	pop    esi
  7fb3f6:	6a 00                	push   0x0
  7fb3f8:	6a 00                	push   0x0
  7fb3fa:	6a 00                	push   0x0
  7fb3fc:	6a 00                	push   0x0
  7fb3fe:	8d 45 f0             	lea    eax,[ebp-0x10]
  7fb401:	e8 56 89 ff ff       	call   0x7f3d5c
  7fb406:	56                   	push   esi
  7fb407:	57                   	push   edi
  7fb408:	8d be 8c 00 00 00    	lea    edi,[esi+0x8c]
  7fb40e:	8d 75 f0             	lea    esi,[ebp-0x10]
  7fb411:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb412:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb413:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb414:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb415:	5f                   	pop    edi
  7fb416:	5e                   	pop    esi
  7fb417:	6a 00                	push   0x0
  7fb419:	6a 00                	push   0x0
  7fb41b:	6a 00                	push   0x0
  7fb41d:	6a 00                	push   0x0
  7fb41f:	8d 45 f0             	lea    eax,[ebp-0x10]
  7fb422:	e8 35 89 ff ff       	call   0x7f3d5c
  7fb427:	56                   	push   esi
  7fb428:	57                   	push   edi
  7fb429:	8d be 9c 00 00 00    	lea    edi,[esi+0x9c]
  7fb42f:	8d 75 f0             	lea    esi,[ebp-0x10]
  7fb432:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb433:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb434:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb435:	a5                   	movs   DWORD PTR es:[edi],DWORD PTR ds:[esi]
  7fb436:	5f                   	pop    edi
  7fb437:	5e                   	pop    esi
  7fb438:	33 c0                	xor    eax,eax
  7fb43a:	89 86 ac 00 00 00    	mov    DWORD PTR [esi+0xac],eax
  7fb440:	8b c7                	mov    eax,edi
  7fb442:	84 db                	test   bl,bl
  7fb444:	74 0f                	je     0x7fb455
  7fb446:	e8 25 bd c0 ff       	call   0x407170
  7fb44b:	64 8f 05 00 00 00 00 	pop    DWORD PTR fs:0x0
  7fb452:	83 c4 0c             	add    esp,0xc
  7fb455:	8b c7                	mov    eax,edi
  7fb457:	5f                   	pop    edi
  7fb458:	5e                   	pop    esi
  7fb459:	5b                   	pop    ebx
  7fb45a:	8b e5                	mov    esp,ebp
  7fb45c:	5d                   	pop    ebp
  7fb45d:	c3                   	ret
