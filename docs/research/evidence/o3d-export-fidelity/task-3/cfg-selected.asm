// Bounded evidence excerpt; not compilable source. Original: .superpowers/sdd/2026-11-10-o3d-export-fidelity/native-authorized-seed/func-005efb98.asm
// Original SHA256 3a4b70d89e89ac186c78909750f7012301753771f37c50649b53a13cd4a7101a; original bytes 252146
// Source line ranges (inclusive): [(2229, 2240), (4408, 4499), (4729, 4746), (5338, 5876)]

// BEGIN original lines 2229..2240
005f2042 WAIT
005f2043 OR EDX,0xffffffff
005f2046 MOV EAX,dword ptr [EBP + 0xfffffa3c]
005f204c CALL 0x005ef378
005f2051 JMP 0x005f7afb
005f2056 MOV EAX,dword ptr [EBP + -0x14]
005f2059 MOV EDX,0x5f85d4
005f205e CALL 0x00409150
005f2063 JNZ 0x005f207d
005f2065 MOV EAX,dword ptr [EBP + -0x8]
005f2068 MOV EAX,dword ptr [EAX + 0x38]
005f206b CALL 0x006040d0
// END original lines 2229..2240

// BEGIN original lines 4408..4499
005f45d7 ADD dword ptr [EBP + 0xfffffb98],0x1
005f45de JNO 0x005f45e5
005f45e0 CALL 0x00406964
005f45e5 PUSH EBP
005f45e6 LEA EDX,[EBP + 0xffffeed8]
005f45ec MOV EAX,dword ptr [EBP + 0xfffffb98]
005f45f2 CALL 0x005ef9e4
005f45f7 POP ECX
005f45f8 MOV EDX,dword ptr [EBP + 0xffffeed8]
005f45fe LEA EAX,[EBP + -0x14]
005f4601 MOV ECX,0x0
005f4606 CALL 0x004092cc
005f460b ADD dword ptr [EBP + 0xfffffb98],0x1
005f4612 JNO 0x005f4619
005f4614 CALL 0x00406964
005f4619 PUSH EBP
005f461a LEA EDX,[EBP + 0xffffeed4]
005f4620 MOV EAX,dword ptr [EBP + 0xfffffb98]
005f4626 CALL 0x005ef9e4
005f462b POP ECX
005f462c MOV EDX,dword ptr [EBP + 0xffffeed4]
005f4632 LEA EAX,[EBP + -0x18]
005f4635 MOV ECX,0x0
005f463a CALL 0x004092cc
005f463f LEA EAX,[EBP + 0xffffeed0]
005f4645 MOV EDX,dword ptr [EBP + -0x18]
005f4648 CALL 0x004095f4
005f464d MOV EAX,dword ptr [EBP + 0xffffeed0]
005f4653 CALL 0x0042237c
005f4658 PUSH EAX
005f4659 MOV EAX,dword ptr [EBP + -0x8]
005f465c MOV EAX,dword ptr [EAX + 0x38]
005f465f CALL 0x006040d0
005f4664 MOV EDX,dword ptr [EBP + -0x14]
005f4667 POP ECX
005f4668 CALL 0x007c3eb0
005f466d MOV dword ptr [EBP + 0xfffffbc8],EAX
005f4673 CMP dword ptr [EBP + 0xfffffbc8],0x0
005f467a JL 0x005f46cd
005f467c MOV EAX,dword ptr [EBP + -0x8]
005f467f MOV EAX,dword ptr [EAX + 0x38]
005f4682 CALL 0x006040d0
005f4687 MOV EAX,dword ptr [EAX + 0xec]
005f468d CALL 0x0040a7fc
005f4692 CMP EAX,dword ptr [EBP + 0xfffffbc8]
005f4698 JLE 0x005f46cd
005f469a MOV EAX,dword ptr [EBP + -0x8]
005f469d MOV EAX,dword ptr [EAX + 0x38]
005f46a0 CALL 0x006040d0
005f46a5 MOV EAX,dword ptr [EAX + 0xec]
005f46ab MOV EDX,dword ptr [EBP + 0xfffffbc8]
005f46b1 TEST EAX,EAX
005f46b3 JZ 0x005f46ba
005f46b5 CMP EDX,dword ptr [EAX + -0x4]
005f46b8 JC 0x005f46bf
005f46ba CALL 0x0040695c
005f46bf IMUL EDX,EDX,0x2f
005f46c2 LEA EAX,[EAX + EDX*0x4]
005f46c5 MOV dword ptr [EBP + 0xfffffba0],EAX
005f46cb JMP 0x005f4731
005f46cd XOR EAX,EAX
005f46cf MOV dword ptr [EBP + 0xfffffba0],EAX
005f46d5 PUSH 0x5f8780
005f46da MOV EAX,dword ptr [EBP + -0x8]
005f46dd PUSH dword ptr [EAX + 0x28]
005f46e0 PUSH 0x5f8794
005f46e5 PUSH dword ptr [EBP + -0x14]
005f46e8 PUSH 0x5f87b4
005f46ed MOV EAX,dword ptr [EBP + -0x8]
005f46f0 MOV EAX,dword ptr [EAX + 0x38]
005f46f3 CALL 0x006040d0
005f46f8 PUSH dword ptr [EAX + 0x17c]
005f46fe PUSH 0x5f87dc
005f4703 LEA EAX,[EBP + 0xffffeec8]
005f4709 MOV EDX,0x7
005f470e CALL 0x00409088
005f4713 MOV EDX,dword ptr [EBP + 0xffffeec8]
005f4719 LEA EAX,[EBP + 0xffffeecc]
005f471f CALL 0x004095f4
005f4724 MOV EAX,dword ptr [EBP + 0xffffeecc]
005f472a MOV DL,0x2
005f472c CALL 0x008022c0
005f4731 CMP dword ptr [EBP + 0xfffffba0],0x0
005f4738 JZ 0x005f7afb
005f473e PUSH 0x0
005f4740 MOV EAX,dword ptr [EBP + 0xfffffba0]
005f4746 ADD EAX,0xb0
005f474b MOV ECX,0x1
005f4750 MOV EDX,dword ptr [0x007fa554]
005f4756 CALL 0x0040a9b0
005f475b ADD ESP,0x4
005f475e JMP 0x005f7afb
// END original lines 4408..4499

// BEGIN original lines 4729..4746
005f4b14 MOV EAX,dword ptr [EBP + -0x8]
005f4b17 MOV EAX,dword ptr [EAX + 0x8]
005f4b1a PUSH EAX
005f4b1b MOV EAX,dword ptr [EBP + -0x14]
005f4b1e PUSH EAX
005f4b1f LEA EAX,[EBP + 0xfffffb98]
005f4b25 PUSH EAX
005f4b26 LEA EAX,[EBP + -0x1]
005f4b29 PUSH EAX
005f4b2a MOV EAX,dword ptr [EBP + -0x8]
005f4b2d ADD EAX,0xc
005f4b30 PUSH EAX
005f4b31 MOV EAX,dword ptr [EBP + -0x8]
005f4b34 MOV EDX,dword ptr [EAX + 0x2c]
005f4b37 MOV EAX,[0x00858ce4]
005f4b3c MOV EAX,dword ptr [EAX]
005f4b3e MOV ECX,dword ptr [EBP + 0xfffffba0]
005f4b44 CALL 0x007fbee0
// END original lines 4729..4746

// BEGIN original lines 5338..5876
005f55bf MOV EAX,dword ptr [EBP + -0x14]
005f55c2 MOV EDX,0x5f89c4
005f55c7 CALL 0x00409150
005f55cc JNZ 0x005f5753
005f55d2 CMP dword ptr [EBP + 0xfffffba0],0x0
005f55d9 JZ 0x005f7afb
005f55df ADD dword ptr [EBP + 0xfffffb98],0x1
005f55e6 JNO 0x005f55ed
005f55e8 CALL 0x00406964
005f55ed PUSH EBP
005f55ee LEA EDX,[EBP + 0xffffee24]
005f55f4 MOV EAX,dword ptr [EBP + 0xfffffb98]
005f55fa CALL 0x005ef9e4
005f55ff POP ECX
005f5600 MOV EDX,dword ptr [EBP + 0xffffee24]
005f5606 LEA EAX,[EBP + -0x14]
005f5609 MOV ECX,0x0
005f560e CALL 0x004092cc
005f5613 MOV EAX,dword ptr [EBP + 0xfffffba0]
005f5619 MOV byte ptr [EAX + 0xb],0x1
005f561d MOV EAX,dword ptr [EBP + 0xfffffba0]
005f5623 MOV EAX,dword ptr [EAX + 0x3c]
005f5626 CALL 0x0040a7fc
005f562b MOV dword ptr [EBP + 0xfffffbc8],EAX
005f5631 MOV EAX,dword ptr [EBP + 0xfffffbc8]
005f5637 ADD EAX,0x1
005f563a JNO 0x005f5641
005f563c CALL 0x00406964
005f5641 PUSH EAX
005f5642 MOV EAX,dword ptr [EBP + 0xfffffba0]
005f5648 ADD EAX,0x3c
005f564b MOV ECX,0x1
005f5650 MOV EDX,dword ptr [0x007fa4e4]
005f5656 CALL 0x0040a9b0
005f565b ADD ESP,0x4
005f565e MOV EAX,dword ptr [EBP + 0xfffffbc8]
005f5664 ADD EAX,0x1
005f5667 JNO 0x005f566e
005f5669 CALL 0x00406964
005f566e PUSH EAX
005f566f MOV EAX,dword ptr [EBP + 0xfffffba0]
005f5675 ADD EAX,0x40
005f5678 MOV ECX,0x1
005f567d MOV EDX,dword ptr [0x007fa51c]
005f5683 CALL 0x0040a9b0
005f5688 ADD ESP,0x4
005f568b PUSH 0x0
005f568d PUSH 0x0
005f568f PUSH 0x0
005f5691 MOV EAX,dword ptr [EBP + -0x8]
005f5694 PUSH dword ptr [EAX + 0x2c]
005f5697 PUSH 0x5f838c
005f569c PUSH dword ptr [EBP + -0x14]
005f569f LEA EAX,[EBP + 0xffffee20]
005f56a5 MOV EDX,0x3
005f56aa CALL 0x00409088
005f56af MOV EDX,dword ptr [EBP + 0xffffee20]
005f56b5 MOV EAX,[0x0085989c]
005f56ba MOV EAX,dword ptr [EAX]
005f56bc XOR ECX,ECX
005f56be CALL 0x007f88a4
005f56c3 MOV EDX,dword ptr [EBP + 0xfffffbc8]
005f56c9 MOV ECX,dword ptr [EBP + 0xfffffba0]
005f56cf MOV ECX,dword ptr [ECX + 0x3c]
005f56d2 TEST ECX,ECX
005f56d4 JZ 0x005f56db
005f56d6 CMP EDX,dword ptr [ECX + -0x4]
005f56d9 JC 0x005f56e0
005f56db CALL 0x0040695c
005f56e0 MOV dword ptr [ECX + EDX*0x4],EAX
005f56e3 ADD dword ptr [EBP + 0xfffffb98],0x1
005f56ea JNO 0x005f56f1
005f56ec CALL 0x00406964
005f56f1 PUSH EBP
005f56f2 LEA EDX,[EBP + 0xffffee1c]
005f56f8 MOV EAX,dword ptr [EBP + 0xfffffb98]
005f56fe CALL 0x005ef9e4
005f5703 POP ECX
005f5704 MOV EDX,dword ptr [EBP + 0xffffee1c]
005f570a LEA EAX,[EBP + -0x14]
005f570d MOV ECX,0x0
005f5712 CALL 0x004092cc
005f5717 MOV EDX,dword ptr [EBP + -0x14]
005f571a MOV EAX,dword ptr [EBP + 0x18]
005f571d CALL 0x007f633c
005f5722 MOV dword ptr [EBP + 0xfffffbc0],EAX
005f5728 MOV EAX,dword ptr [EBP + 0xfffffbc8]
005f572e MOV EDX,dword ptr [EBP + 0xfffffba0]
005f5734 MOV EDX,dword ptr [EDX + 0x40]
005f5737 TEST EDX,EDX
005f5739 JZ 0x005f5740
005f573b CMP EAX,dword ptr [EDX + -0x4]
005f573e JC 0x005f5745
005f5740 CALL 0x0040695c
005f5745 MOV ECX,dword ptr [EBP + 0xfffffbc0]
005f574b MOV dword ptr [EDX + EAX*0x4],ECX
005f574e JMP 0x005f7afb
005f5753 MOV EAX,dword ptr [EBP + -0x14]
005f5756 MOV EDX,0x5f89e0
005f575b CALL 0x00409150
005f5760 JNZ 0x005f5804
005f5766 CMP dword ptr [EBP + 0xfffffba0],0x0
005f576d JZ 0x005f7afb
005f5773 ADD dword ptr [EBP + 0xfffffb98],0x1
005f577a JNO 0x005f5781
005f577c CALL 0x00406964
005f5781 PUSH EBP
005f5782 LEA EDX,[EBP + 0xffffee18]
005f5788 MOV EAX,dword ptr [EBP + 0xfffffb98]
005f578e CALL 0x005ef9e4
005f5793 POP ECX
005f5794 MOV EDX,dword ptr [EBP + 0xffffee18]
005f579a LEA EAX,[EBP + -0x14]
005f579d MOV ECX,0x0
005f57a2 CALL 0x004092cc
005f57a7 MOV EAX,dword ptr [EBP + 0xfffffba0]
005f57ad MOV byte ptr [EAX + 0xa],0x1
005f57b1 PUSH 0x0
005f57b3 PUSH 0x0
005f57b5 PUSH 0x0
005f57b7 MOV EAX,dword ptr [EBP + -0x8]
005f57ba PUSH dword ptr [EAX + 0x2c]
005f57bd PUSH 0x5f838c
005f57c2 PUSH dword ptr [EBP + -0x14]
005f57c5 LEA EAX,[EBP + 0xffffee14]
005f57cb MOV EDX,0x3
005f57d0 CALL 0x00409088
005f57d5 MOV EDX,dword ptr [EBP + 0xffffee14]
005f57db MOV EAX,[0x0085989c]
005f57e0 MOV EAX,dword ptr [EAX]
005f57e2 MOV CL,0x1
005f57e4 CALL 0x007f88a4
005f57e9 MOV EDX,dword ptr [EBP + 0xfffffba0]
005f57ef MOV dword ptr [EDX + 0x34],EAX
005f57f2 MOV EAX,dword ptr [EBP + 0xfffffba0]
005f57f8 MOV dword ptr [EAX + 0x38],0xffffffff
005f57ff JMP 0x005f7afb
005f5804 MOV EAX,dword ptr [EBP + -0x14]
005f5807 MOV EDX,0x5f89e0
005f580c CALL 0x00409150
005f5811 JNZ 0x005f58fc
005f5817 CMP dword ptr [EBP + 0xfffffba0],0x0
005f581e JZ 0x005f7afb
005f5824 ADD dword ptr [EBP + 0xfffffb98],0x1
005f582b JNO 0x005f5832
005f582d CALL 0x00406964
005f5832 PUSH EBP
005f5833 LEA EDX,[EBP + 0xffffee10]
005f5839 MOV EAX,dword ptr [EBP + 0xfffffb98]
005f583f CALL 0x005ef9e4
005f5844 POP ECX
005f5845 MOV EDX,dword ptr [EBP + 0xffffee10]
005f584b LEA EAX,[EBP + -0x14]
005f584e MOV ECX,0x0
005f5853 CALL 0x004092cc
005f5858 MOV EAX,dword ptr [EBP + 0xfffffba0]
005f585e MOV byte ptr [EAX + 0xa],0x1
005f5862 PUSH 0x0
005f5864 PUSH 0x0
005f5866 PUSH 0x0
005f5868 MOV EAX,dword ptr [EBP + -0x8]
005f586b PUSH dword ptr [EAX + 0x2c]
005f586e PUSH 0x5f838c
005f5873 PUSH dword ptr [EBP + -0x14]
005f5876 LEA EAX,[EBP + 0xffffee0c]
005f587c MOV EDX,0x3
005f5881 CALL 0x00409088
005f5886 MOV EDX,dword ptr [EBP + 0xffffee0c]
005f588c MOV EAX,[0x0085989c]
005f5891 MOV EAX,dword ptr [EAX]
005f5893 MOV CL,0x1
005f5895 CALL 0x007f88a4
005f589a MOV EDX,dword ptr [EBP + 0xfffffba0]
005f58a0 MOV dword ptr [EDX + 0x34],EAX
005f58a3 ADD dword ptr [EBP + 0xfffffb98],0x1
005f58aa JNO 0x005f58b1
005f58ac CALL 0x00406964
005f58b1 PUSH EBP
005f58b2 LEA EDX,[EBP + 0xffffee08]
005f58b8 MOV EAX,dword ptr [EBP + 0xfffffb98]
005f58be CALL 0x005ef9e4
005f58c3 POP ECX
005f58c4 MOV EDX,dword ptr [EBP + 0xffffee08]
005f58ca LEA EAX,[EBP + -0x14]
005f58cd MOV ECX,0x0
005f58d2 CALL 0x004092cc
005f58d7 MOV EDX,dword ptr [EBP + -0x14]
005f58da MOV EAX,dword ptr [EBP + 0x18]
005f58dd CALL 0x007f633c
005f58e2 MOV dword ptr [EBP + 0xfffffbc0],EAX
005f58e8 MOV EAX,dword ptr [EBP + 0xfffffba0]
005f58ee MOV EDX,dword ptr [EBP + 0xfffffbc0]
005f58f4 MOV dword ptr [EAX + 0x38],EDX
005f58f7 JMP 0x005f7afb
005f58fc MOV EAX,dword ptr [EBP + -0x14]
005f58ff MOV EDX,0x5f89fc
005f5904 CALL 0x00409150
005f5909 JNZ 0x005f5f08
005f590f CMP dword ptr [EBP + 0xfffffba0],0x0
005f5916 JZ 0x005f7afb
005f591c ADD dword ptr [EBP + 0xfffffb98],0x1
005f5923 JNO 0x005f592a
005f5925 CALL 0x00406964
005f592a PUSH EBP
005f592b LEA EDX,[EBP + 0xffffee04]
005f5931 MOV EAX,dword ptr [EBP + 0xfffffb98]
005f5937 CALL 0x005ef9e4
005f593c POP ECX
005f593d MOV EDX,dword ptr [EBP + 0xffffee04]
005f5943 LEA EAX,[EBP + -0x14]
005f5946 MOV ECX,0x0
005f594b CALL 0x004092cc
005f5950 LEA EAX,[EBP + 0xfffffecc]
005f5956 MOV EDX,dword ptr [EBP + -0x14]
005f5959 CALL 0x004095f4
005f595e MOV EDX,dword ptr [0x00859840]
005f5964 MOV EAX,dword ptr [EBP + 0xfffffecc]
005f596a CALL 0x00424f68
005f596f FSTP extended double ptr [EBP + 0xfffff6b0]
005f5975 WAIT
005f5976 FLD extended double ptr [EBP + 0xfffff6b0]
005f597c MOV EAX,dword ptr [EBP + 0xfffffba0]
005f5982 FSTP float ptr [EAX + 0x6c]
005f5985 WAIT
005f5986 ADD dword ptr [EBP + 0xfffffb98],0x1
005f598d JNO 0x005f5994
005f598f CALL 0x00406964
005f5994 PUSH EBP
005f5995 LEA EDX,[EBP + 0xffffee00]
005f599b MOV EAX,dword ptr [EBP + 0xfffffb98]
005f59a1 CALL 0x005ef9e4
005f59a6 POP ECX
005f59a7 MOV EDX,dword ptr [EBP + 0xffffee00]
005f59ad LEA EAX,[EBP + -0x14]
005f59b0 MOV ECX,0x0
005f59b5 CALL 0x004092cc
005f59ba LEA EAX,[EBP + 0xfffffec8]
005f59c0 MOV EDX,dword ptr [EBP + -0x14]
005f59c3 CALL 0x004095f4
005f59c8 MOV EDX,dword ptr [0x00859840]
005f59ce MOV EAX,dword ptr [EBP + 0xfffffec8]
005f59d4 CALL 0x00424f68
005f59d9 FSTP extended double ptr [EBP + 0xfffff6a0]
005f59df WAIT
005f59e0 FLD extended double ptr [EBP + 0xfffff6a0]
005f59e6 MOV EAX,dword ptr [EBP + 0xfffffba0]
005f59ec FSTP float ptr [EAX + 0x70]
005f59ef WAIT
005f59f0 ADD dword ptr [EBP + 0xfffffb98],0x1
005f59f7 JNO 0x005f59fe
005f59f9 CALL 0x00406964
005f59fe PUSH EBP
005f59ff LEA EDX,[EBP + 0xffffedfc]
005f5a05 MOV EAX,dword ptr [EBP + 0xfffffb98]
005f5a0b CALL 0x005ef9e4
005f5a10 POP ECX
005f5a11 MOV EDX,dword ptr [EBP + 0xffffedfc]
005f5a17 LEA EAX,[EBP + -0x14]
005f5a1a MOV ECX,0x0
005f5a1f CALL 0x004092cc
005f5a24 LEA EAX,[EBP + 0xfffffec4]
005f5a2a MOV EDX,dword ptr [EBP + -0x14]
005f5a2d CALL 0x004095f4
005f5a32 MOV EDX,dword ptr [0x00859840]
005f5a38 MOV EAX,dword ptr [EBP + 0xfffffec4]
005f5a3e CALL 0x00424f68
005f5a43 FSTP extended double ptr [EBP + 0xfffff690]
005f5a49 WAIT
005f5a4a FLD extended double ptr [EBP + 0xfffff690]
005f5a50 MOV EAX,dword ptr [EBP + 0xfffffba0]
005f5a56 FSTP float ptr [EAX + 0x74]
005f5a59 WAIT
005f5a5a ADD dword ptr [EBP + 0xfffffb98],0x1
005f5a61 JNO 0x005f5a68
005f5a63 CALL 0x00406964
005f5a68 PUSH EBP
005f5a69 LEA EDX,[EBP + 0xffffedf8]
005f5a6f MOV EAX,dword ptr [EBP + 0xfffffb98]
005f5a75 CALL 0x005ef9e4
005f5a7a POP ECX
005f5a7b MOV EDX,dword ptr [EBP + 0xffffedf8]
005f5a81 LEA EAX,[EBP + -0x14]
005f5a84 MOV ECX,0x0
005f5a89 CALL 0x004092cc
005f5a8e LEA EAX,[EBP + 0xfffffec0]
005f5a94 MOV EDX,dword ptr [EBP + -0x14]
005f5a97 CALL 0x004095f4
005f5a9c MOV EDX,dword ptr [0x00859840]
005f5aa2 MOV EAX,dword ptr [EBP + 0xfffffec0]
005f5aa8 CALL 0x00424f68
005f5aad FSTP extended double ptr [EBP + 0xfffff680]
005f5ab3 WAIT
005f5ab4 FLD extended double ptr [EBP + 0xfffff680]
005f5aba MOV EAX,dword ptr [EBP + 0xfffffba0]
005f5ac0 FSTP float ptr [EAX + 0x78]
005f5ac3 WAIT
005f5ac4 ADD dword ptr [EBP + 0xfffffb98],0x1
005f5acb JNO 0x005f5ad2
005f5acd CALL 0x00406964
005f5ad2 PUSH EBP
005f5ad3 LEA EDX,[EBP + 0xffffedf4]
005f5ad9 MOV EAX,dword ptr [EBP + 0xfffffb98]
005f5adf CALL 0x005ef9e4
005f5ae4 POP ECX
005f5ae5 MOV EDX,dword ptr [EBP + 0xffffedf4]
005f5aeb LEA EAX,[EBP + -0x14]
005f5aee MOV ECX,0x0
005f5af3 CALL 0x004092cc
005f5af8 LEA EAX,[EBP + 0xfffffebc]
005f5afe MOV EDX,dword ptr [EBP + -0x14]
005f5b01 CALL 0x004095f4
005f5b06 MOV EDX,dword ptr [0x00859840]
005f5b0c MOV EAX,dword ptr [EBP + 0xfffffebc]
005f5b12 CALL 0x00424f68
005f5b17 FSTP extended double ptr [EBP + 0xfffff670]
005f5b1d WAIT
005f5b1e FLD extended double ptr [EBP + 0xfffff670]
005f5b24 MOV EAX,dword ptr [EBP + 0xfffffba0]
005f5b2a FSTP float ptr [EAX + 0x7c]
005f5b2d WAIT
005f5b2e ADD dword ptr [EBP + 0xfffffb98],0x1
005f5b35 JNO 0x005f5b3c
005f5b37 CALL 0x00406964
005f5b3c PUSH EBP
005f5b3d LEA EDX,[EBP + 0xffffedf0]
005f5b43 MOV EAX,dword ptr [EBP + 0xfffffb98]
005f5b49 CALL 0x005ef9e4
005f5b4e POP ECX
005f5b4f MOV EDX,dword ptr [EBP + 0xffffedf0]
005f5b55 LEA EAX,[EBP + -0x14]
005f5b58 MOV ECX,0x0
005f5b5d CALL 0x004092cc
005f5b62 LEA EAX,[EBP + 0xfffffeb8]
005f5b68 MOV EDX,dword ptr [EBP + -0x14]
005f5b6b CALL 0x004095f4
005f5b70 MOV EDX,dword ptr [0x00859840]
005f5b76 MOV EAX,dword ptr [EBP + 0xfffffeb8]
005f5b7c CALL 0x00424f68
005f5b81 FSTP extended double ptr [EBP + 0xfffff660]
005f5b87 WAIT
005f5b88 FLD extended double ptr [EBP + 0xfffff660]
005f5b8e MOV EAX,dword ptr [EBP + 0xfffffba0]
005f5b94 FSTP float ptr [EAX + 0x80]
005f5b9a WAIT
005f5b9b ADD dword ptr [EBP + 0xfffffb98],0x1
005f5ba2 JNO 0x005f5ba9
005f5ba4 CALL 0x00406964
005f5ba9 PUSH EBP
005f5baa LEA EDX,[EBP + 0xffffedec]
005f5bb0 MOV EAX,dword ptr [EBP + 0xfffffb98]
005f5bb6 CALL 0x005ef9e4
005f5bbb POP ECX
005f5bbc MOV EDX,dword ptr [EBP + 0xffffedec]
005f5bc2 LEA EAX,[EBP + -0x14]
005f5bc5 MOV ECX,0x0
005f5bca CALL 0x004092cc
005f5bcf LEA EAX,[EBP + 0xfffffeb4]
005f5bd5 MOV EDX,dword ptr [EBP + -0x14]
005f5bd8 CALL 0x004095f4
005f5bdd MOV EDX,dword ptr [0x00859840]
005f5be3 MOV EAX,dword ptr [EBP + 0xfffffeb4]
005f5be9 CALL 0x00424f68
005f5bee FSTP extended double ptr [EBP + 0xfffff650]
005f5bf4 WAIT
005f5bf5 FLD extended double ptr [EBP + 0xfffff650]
005f5bfb MOV EAX,dword ptr [EBP + 0xfffffba0]
005f5c01 FSTP float ptr [EAX + 0x84]
005f5c07 WAIT
005f5c08 ADD dword ptr [EBP + 0xfffffb98],0x1
005f5c0f JNO 0x005f5c16
005f5c11 CALL 0x00406964
005f5c16 PUSH EBP
005f5c17 LEA EDX,[EBP + 0xffffede8]
005f5c1d MOV EAX,dword ptr [EBP + 0xfffffb98]
005f5c23 CALL 0x005ef9e4
005f5c28 POP ECX
005f5c29 MOV EDX,dword ptr [EBP + 0xffffede8]
005f5c2f LEA EAX,[EBP + -0x14]
005f5c32 MOV ECX,0x0
005f5c37 CALL 0x004092cc
005f5c3c LEA EAX,[EBP + 0xfffffeb0]
005f5c42 MOV EDX,dword ptr [EBP + -0x14]
005f5c45 CALL 0x004095f4
005f5c4a MOV EDX,dword ptr [0x00859840]
005f5c50 MOV EAX,dword ptr [EBP + 0xfffffeb0]
005f5c56 CALL 0x00424f68
005f5c5b FSTP extended double ptr [EBP + 0xfffff640]
005f5c61 WAIT
005f5c62 FLD extended double ptr [EBP + 0xfffff640]
005f5c68 MOV EAX,dword ptr [EBP + 0xfffffba0]
005f5c6e FSTP float ptr [EAX + 0x8c]
005f5c74 WAIT
005f5c75 ADD dword ptr [EBP + 0xfffffb98],0x1
005f5c7c JNO 0x005f5c83
005f5c7e CALL 0x00406964
005f5c83 PUSH EBP
005f5c84 LEA EDX,[EBP + 0xffffede4]
005f5c8a MOV EAX,dword ptr [EBP + 0xfffffb98]
005f5c90 CALL 0x005ef9e4
005f5c95 POP ECX
005f5c96 MOV EDX,dword ptr [EBP + 0xffffede4]
005f5c9c LEA EAX,[EBP + -0x14]
005f5c9f MOV ECX,0x0
005f5ca4 CALL 0x004092cc
005f5ca9 LEA EAX,[EBP + 0xfffffeac]
005f5caf MOV EDX,dword ptr [EBP + -0x14]
005f5cb2 CALL 0x004095f4
005f5cb7 MOV EDX,dword ptr [0x00859840]
005f5cbd MOV EAX,dword ptr [EBP + 0xfffffeac]
005f5cc3 CALL 0x00424f68
005f5cc8 FSTP extended double ptr [EBP + 0xfffff630]
005f5cce WAIT
005f5ccf FLD extended double ptr [EBP + 0xfffff630]
005f5cd5 MOV EAX,dword ptr [EBP + 0xfffffba0]
005f5cdb FSTP float ptr [EAX + 0x90]
005f5ce1 WAIT
005f5ce2 ADD dword ptr [EBP + 0xfffffb98],0x1
005f5ce9 JNO 0x005f5cf0
005f5ceb CALL 0x00406964
005f5cf0 PUSH EBP
005f5cf1 LEA EDX,[EBP + 0xffffede0]
005f5cf7 MOV EAX,dword ptr [EBP + 0xfffffb98]
005f5cfd CALL 0x005ef9e4
005f5d02 POP ECX
005f5d03 MOV EDX,dword ptr [EBP + 0xffffede0]
005f5d09 LEA EAX,[EBP + -0x14]
005f5d0c MOV ECX,0x0
005f5d11 CALL 0x004092cc
005f5d16 LEA EAX,[EBP + 0xfffffea8]
005f5d1c MOV EDX,dword ptr [EBP + -0x14]
005f5d1f CALL 0x004095f4
005f5d24 MOV EDX,dword ptr [0x00859840]
005f5d2a MOV EAX,dword ptr [EBP + 0xfffffea8]
005f5d30 CALL 0x00424f68
005f5d35 FSTP extended double ptr [EBP + 0xfffff620]
005f5d3b WAIT
005f5d3c FLD extended double ptr [EBP + 0xfffff620]
005f5d42 MOV EAX,dword ptr [EBP + 0xfffffba0]
005f5d48 FSTP float ptr [EAX + 0x94]
005f5d4e WAIT
005f5d4f ADD dword ptr [EBP + 0xfffffb98],0x1
005f5d56 JNO 0x005f5d5d
005f5d58 CALL 0x00406964
005f5d5d PUSH EBP
005f5d5e LEA EDX,[EBP + 0xffffeddc]
005f5d64 MOV EAX,dword ptr [EBP + 0xfffffb98]
005f5d6a CALL 0x005ef9e4
005f5d6f POP ECX
005f5d70 MOV EDX,dword ptr [EBP + 0xffffeddc]
005f5d76 LEA EAX,[EBP + -0x14]
005f5d79 MOV ECX,0x0
005f5d7e CALL 0x004092cc
005f5d83 LEA EAX,[EBP + 0xfffffea4]
005f5d89 MOV EDX,dword ptr [EBP + -0x14]
005f5d8c CALL 0x004095f4
005f5d91 MOV EDX,dword ptr [0x00859840]
005f5d97 MOV EAX,dword ptr [EBP + 0xfffffea4]
005f5d9d CALL 0x00424f68
005f5da2 FSTP extended double ptr [EBP + 0xfffff610]
005f5da8 WAIT
005f5da9 FLD extended double ptr [EBP + 0xfffff610]
005f5daf MOV EAX,dword ptr [EBP + 0xfffffba0]
005f5db5 FSTP float ptr [EAX + 0x9c]
005f5dbb WAIT
005f5dbc ADD dword ptr [EBP + 0xfffffb98],0x1
005f5dc3 JNO 0x005f5dca
005f5dc5 CALL 0x00406964
005f5dca PUSH EBP
005f5dcb LEA EDX,[EBP + 0xffffedd8]
005f5dd1 MOV EAX,dword ptr [EBP + 0xfffffb98]
005f5dd7 CALL 0x005ef9e4
005f5ddc POP ECX
005f5ddd MOV EDX,dword ptr [EBP + 0xffffedd8]
005f5de3 LEA EAX,[EBP + -0x14]
005f5de6 MOV ECX,0x0
005f5deb CALL 0x004092cc
005f5df0 LEA EAX,[EBP + 0xfffffea0]
005f5df6 MOV EDX,dword ptr [EBP + -0x14]
005f5df9 CALL 0x004095f4
005f5dfe MOV EDX,dword ptr [0x00859840]
005f5e04 MOV EAX,dword ptr [EBP + 0xfffffea0]
005f5e0a CALL 0x00424f68
005f5e0f FSTP extended double ptr [EBP + 0xfffff600]
005f5e15 WAIT
005f5e16 FLD extended double ptr [EBP + 0xfffff600]
005f5e1c MOV EAX,dword ptr [EBP + 0xfffffba0]
005f5e22 FSTP float ptr [EAX + 0xa0]
005f5e28 WAIT
005f5e29 ADD dword ptr [EBP + 0xfffffb98],0x1
005f5e30 JNO 0x005f5e37
005f5e32 CALL 0x00406964
005f5e37 PUSH EBP
005f5e38 LEA EDX,[EBP + 0xffffedd4]
005f5e3e MOV EAX,dword ptr [EBP + 0xfffffb98]
005f5e44 CALL 0x005ef9e4
005f5e49 POP ECX
005f5e4a MOV EDX,dword ptr [EBP + 0xffffedd4]
005f5e50 LEA EAX,[EBP + -0x14]
005f5e53 MOV ECX,0x0
005f5e58 CALL 0x004092cc
005f5e5d LEA EAX,[EBP + 0xfffffe9c]
005f5e63 MOV EDX,dword ptr [EBP + -0x14]
005f5e66 CALL 0x004095f4
005f5e6b MOV EDX,dword ptr [0x00859840]
005f5e71 MOV EAX,dword ptr [EBP + 0xfffffe9c]
005f5e77 CALL 0x00424f68
005f5e7c FSTP extended double ptr [EBP + 0xfffff5f0]
005f5e82 WAIT
005f5e83 FLD extended double ptr [EBP + 0xfffff5f0]
005f5e89 MOV EAX,dword ptr [EBP + 0xfffffba0]
005f5e8f FSTP float ptr [EAX + 0xa4]
005f5e95 WAIT
005f5e96 ADD dword ptr [EBP + 0xfffffb98],0x1
005f5e9d JNO 0x005f5ea4
005f5e9f CALL 0x00406964
005f5ea4 PUSH EBP
005f5ea5 LEA EDX,[EBP + 0xffffedd0]
005f5eab MOV EAX,dword ptr [EBP + 0xfffffb98]
005f5eb1 CALL 0x005ef9e4
005f5eb6 POP ECX
005f5eb7 MOV EDX,dword ptr [EBP + 0xffffedd0]
005f5ebd LEA EAX,[EBP + -0x14]
005f5ec0 MOV ECX,0x0
005f5ec5 CALL 0x004092cc
005f5eca LEA EAX,[EBP + 0xfffffe98]
005f5ed0 MOV EDX,dword ptr [EBP + -0x14]
005f5ed3 CALL 0x004095f4
005f5ed8 MOV EDX,dword ptr [0x00859840]
005f5ede MOV EAX,dword ptr [EBP + 0xfffffe98]
005f5ee4 CALL 0x00424f68
005f5ee9 FSTP extended double ptr [EBP + 0xfffff5e0]
005f5eef WAIT
005f5ef0 FLD extended double ptr [EBP + 0xfffff5e0]
005f5ef6 MOV EAX,dword ptr [EBP + 0xfffffba0]
005f5efc FSTP float ptr [EAX + 0xac]
005f5f02 WAIT
005f5f03 JMP 0x005f7afb
005f5f08 MOV EAX,dword ptr [EBP + -0x14]
005f5f0b MOV EDX,0x5f8a18
// END original lines 5338..5876
