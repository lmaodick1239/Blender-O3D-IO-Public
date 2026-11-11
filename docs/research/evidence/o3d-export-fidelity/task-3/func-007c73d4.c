// 007c73d4 FUN_007c73d4 SHA256 c7765877620816dd4de4cceb21dce1996c8789c89ee550c1fb58440ee689a33e

void FUN_007c73d4(int param_1,undefined4 param_2,char param_3,int *param_4,char param_5,uint param_6
                 )

{
  uint uVar1;
  undefined1 *puVar2;
  char cVar3;
  int iVar4;
  undefined4 uVar5;
  uint *puVar6;
  uint uVar7;
  undefined4 *in_FS_OFFSET;
  undefined4 uStack_28;
  undefined1 *puStack_24;
  undefined1 *puStack_20;
  undefined4 local_c;
  undefined4 local_8;
  
  local_c = 0;
  puStack_20 = (undefined1 *)0x7c73f1;
  local_8 = param_2;
  FUN_0040ab38(param_2);
  puStack_20 = (undefined1 *)0x7c73f9;
  FUN_0040c0c4(param_4);
  puStack_24 = &LAB_007c76a1;
  uStack_28 = *in_FS_OFFSET;
  *in_FS_OFFSET = &uStack_28;
  puStack_20 = &stack0xfffffffc;
  cVar3 = FUN_00805c78(0x5b);
  if ((cVar3 != '\0') && (*(int *)(param_1 + 0xa0) != 0)) {
    if (param_5 != '\0') {
      FUN_007c3194(param_1);
    }
    uVar1 = param_6;
    if (param_3 != '\0') {
      puVar6 = (uint *)PTR_DAT_008592a8;
      if (*PTR_DAT_00858be4 == '\0') {
        iVar4 = *(int *)(param_1 + 0xec);
        if ((iVar4 == 0) || (*(uint *)(iVar4 + -4) <= param_6)) {
                    /* WARNING: Subroutine does not return */
          thunk_FUN_00404770();
        }
        puVar6 = (uint *)(iVar4 + param_6 * 0xbc);
      }
      FUN_0040c050(&local_c);
      if ((((*PTR_DAT_00858c98 != '\0') && (puVar6 != (uint *)0x0)) &&
          (*(char *)((int)puVar6 + 9) != '\0')) &&
         (iVar4 = FUN_0040a7fc(*(undefined4 *)PTR_DAT_008590d8),
         (int)(uint)*(byte *)((int)puVar6 + 0x31) < iVar4)) {
        iVar4 = *(int *)PTR_DAT_008590d8;
        if ((iVar4 == 0) || (*(uint *)(iVar4 + -4) <= (uint)*(byte *)((int)puVar6 + 0x31))) {
                    /* WARNING: Subroutine does not return */
          thunk_FUN_00404770();
        }
        FUN_0040c068(&local_c,*(undefined4 *)(iVar4 + (uint)*(byte *)((int)puVar6 + 0x31) * 4));
      }
      if (puVar6 != (uint *)0x0) {
        uVar7 = *puVar6;
        if (-1 < (int)uVar7) {
          iVar4 = *(int *)(*(int *)PTR_DAT_0085989c + 8);
          if ((iVar4 == 0) || (*(uint *)(iVar4 + -4) <= uVar7)) {
                    /* WARNING: Subroutine does not return */
            thunk_FUN_00404770();
          }
          if (((*(char *)(iVar4 + 0x5e + uVar7 * 0x68) != '\0') && (*PTR_DAT_00859e9c != '\0')) &&
             (*(char *)(*(int *)PTR_DAT_00859448 + 0x148) != '\0')) {
            uVar7 = 0;
            do {
              iVar4 = *(int *)(*(int *)PTR_DAT_0085989c + 8);
              if ((iVar4 == 0) || (*(uint *)(iVar4 + -4) <= *puVar6)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              if ((*(char *)(iVar4 + 0x5f + *puVar6 * 0x68) == '\0') && (uVar7 == 1)) break;
              if (0xff < uVar7) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              FUN_007fc878(*(undefined4 *)PTR_DAT_00858ce4,puVar6);
              if (*(int *)(param_1 + 0xa0) == 0) {
                FUN_00802794("Nilles Mesh (Prerender)!",2);
              }
              else {
                cVar3 = FUN_00805c78(0x5a);
                if (cVar3 != '\0') {
                  if ((int)uVar1 < 0) {
                    /* WARNING: Subroutine does not return */
                    thunk_FUN_00404770();
                  }
                  (**(code **)(**(int **)(param_1 + 0xa0) + 0xc))();
                }
              }
              uVar7 = uVar7 + 1;
            } while (uVar7 != 2);
          }
        }
        FUN_007fd9b0(*(undefined4 *)PTR_DAT_00858ce4,puVar6,local_c,&local_8);
      }
      FUN_0040c050(&local_c);
    }
    if (*PTR_DAT_00859e08 != '\0') {
      uVar5 = (**(code **)(**(int **)PTR_DAT_00859508 + 0x104))();
      FUN_008029ac(uVar5,"Shader: Commit Changes",3);
    }
    if (param_4 == (int *)0x0) {
      cVar3 = FUN_00805c78(0x5a);
      if (cVar3 == '\0') {
        uVar5 = 0;
      }
      else {
        if ((int)uVar1 < 0) {
                    /* WARNING: Subroutine does not return */
          thunk_FUN_00404770();
        }
        uVar5 = (**(code **)(**(int **)(param_1 + 0xa0) + 0xc))();
      }
      FUN_008029ac(uVar5,"Draw Normal Mesh",3);
    }
    else {
      cVar3 = FUN_00805c78(0x5a);
      if (cVar3 == '\0') {
        uVar5 = 0;
      }
      else {
        if ((int)uVar1 < 0) {
                    /* WARNING: Subroutine does not return */
          thunk_FUN_00404770();
        }
        uVar5 = (**(code **)(*param_4 + 0xc))();
      }
      FUN_008029ac(uVar5,"Draw Skinned Mesh",3);
    }
  }
  puVar2 = puStack_20;
  *in_FS_OFFSET = uStack_28;
  puStack_20 = &LAB_007c76a8;
  puStack_24 = (undefined1 *)0x7c768a;
  FUN_0040c050(&local_c,uStack_28,puVar2);
  puStack_24 = (undefined1 *)0x7c7698;
  FUN_0040aad4(&local_8,&DAT_007c1a70);
  puStack_24 = (undefined1 *)0x7c76a0;
  FUN_0040c050(&param_4);
  return;
}


