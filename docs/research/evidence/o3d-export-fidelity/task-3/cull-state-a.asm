
/mnt/Random/users/user/Documents/Ghidra/OMSI/Omsi.exe:     file format pei-i386


Disassembly of section .text:

005cbe70 <.text+0x1cae70>:
  5cbe70:	ba 08 00 00 00       	mov    edx,0x8
  5cbe75:	e8 06 4f 23 00       	call   0x800d80
  5cbe7a:	8d 45 fc             	lea    eax,[ebp-0x4]
  5cbe7d:	50                   	push   eax
  5cbe7e:	6a 16                	push   0x16
  5cbe80:	a1 24 88 85 00       	mov    eax,ds:0x858824
  5cbe85:	8b 00                	mov    eax,DWORD PTR [eax]
  5cbe87:	50                   	push   eax
  5cbe88:	8b 00                	mov    eax,DWORD PTR [eax]
  5cbe8a:	ff 90 e8 00 00 00    	call   DWORD PTR [eax+0xe8]
  5cbe90:	a1 e4 8c 85 00       	mov    eax,ds:0x858ce4
  5cbe95:	8b 00                	mov    eax,DWORD PTR [eax]
  5cbe97:	b9 01 00 00 00       	mov    ecx,0x1
  5cbe9c:	ba 16 00 00 00       	mov    edx,0x16
  5cbea1:	e8 da 4e 23 00       	call   0x800d80
  5cbea6:	6a 00                	push   0x0
  5cbea8:	8b 46 60             	mov    eax,DWORD PTR [esi+0x60]
  5cbeab:	50                   	push   eax
  5cbeac:	8b 00                	mov    eax,DWORD PTR [eax]
  5cbeae:	ff 50 0c             	call   DWORD PTR [eax+0xc]
  5cbeb1:	a1 e4 8c 85 00       	mov    eax,ds:0x858ce4
  5cbeb6:	8b 00                	mov    eax,DWORD PTR [eax]
  5cbeb8:	b9 03 00 00 00       	mov    ecx,0x3
  5cbebd:	ba 08 00 00 00       	mov    edx,0x8
  5cbec2:	e8 b9 4e 23 00       	call   0x800d80
  5cbec7:	a1 e4 8c 85 00       	mov    eax,ds:0x858ce4
  5cbecc:	8b 00                	mov    eax,DWORD PTR [eax]
  5cbece:	8b 4d fc             	mov    ecx,DWORD PTR [ebp-0x4]
  5cbed1:	ba 16 00 00 00       	mov    edx,0x16
  5cbed6:	e8 a5 4e 23 00       	call   0x800d80
  5cbedb:	5f                   	pop    edi
  5cbedc:	5e                   	pop    esi
  5cbedd:	8b e5                	mov    esp,ebp
  5cbedf:	5d                   	pop    ebp
