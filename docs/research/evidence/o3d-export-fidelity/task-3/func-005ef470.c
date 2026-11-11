// 005ef470 FUN_005ef470 SHA256 c7765877620816dd4de4cceb21dce1996c8789c89ee550c1fb58440ee689a33e

void FUN_005ef470(int param_1,int param_2)

{
  int iVar1;
  undefined1 *puVar2;
  undefined4 uVar3;
  undefined1 *puVar4;
  undefined1 local_84 [64];
  undefined1 local_44 [64];
  
  if (param_2 == -1) {
    iVar1 = *(int *)(*(int *)(param_1 + 0x198) + 0xc);
    param_2 = iVar1 + -1;
    if (SBORROW4(iVar1,1)) {
                    /* WARNING: Subroutine does not return */
      thunk_FUN_00404770();
    }
  }
  FUN_005fedc8(*(undefined4 *)(param_1 + 0x198),param_2,param_1 + 0x60);
  FUN_005fed88(*(undefined4 *)(param_1 + 0x198),param_2,local_84);
  puVar4 = local_84;
  uVar3 = 0;
  puVar2 = local_44;
  D3DXMatrixInverse();
  FUN_005fedc8(*(undefined4 *)(param_1 + 0x19c),param_2,local_44,puVar2,uVar3,puVar4);
  return;
}


