// 007fbee0 FUN_007fbee0 SHA256 c7765877620816dd4de4cceb21dce1996c8789c89ee550c1fb58440ee689a33e

/* WARNING: Removing unreachable block (ram,0x007fbf9c) */
/* WARNING: Removing unreachable block (ram,0x007fc003) */
/* WARNING: Removing unreachable block (ram,0x007fc110) */
/* WARNING: Removing unreachable block (ram,0x007fc11d) */
/* WARNING: Removing unreachable block (ram,0x007fc122) */
/* WARNING: Removing unreachable block (ram,0x007fc256) */
/* WARNING: Removing unreachable block (ram,0x007fc25b) */
/* WARNING: Removing unreachable block (ram,0x007fc260) */
/* WARNING: Removing unreachable block (ram,0x007fc294) */
/* WARNING: Removing unreachable block (ram,0x007fc183) */
/* WARNING: Removing unreachable block (ram,0x007fc188) */
/* WARNING: Removing unreachable block (ram,0x007fc18d) */
/* WARNING: Removing unreachable block (ram,0x007fc1bd) */
/* WARNING: Removing unreachable block (ram,0x007fc1ef) */
/* WARNING: Removing unreachable block (ram,0x007fc1f4) */
/* WARNING: Removing unreachable block (ram,0x007fc1f9) */
/* WARNING: Removing unreachable block (ram,0x007fc039) */
/* WARNING: Removing unreachable block (ram,0x007fc03e) */
/* WARNING: Removing unreachable block (ram,0x007fc043) */
/* WARNING: Removing unreachable block (ram,0x007fc077) */
/* WARNING: Removing unreachable block (ram,0x007fc0a9) */
/* WARNING: Removing unreachable block (ram,0x007fc0ae) */
/* WARNING: Removing unreachable block (ram,0x007fc0b3) */
/* WARNING: Removing unreachable block (ram,0x007fbfbc) */
/* WARNING: Removing unreachable block (ram,0x007fbf5e) */
/* WARNING: Removing unreachable block (ram,0x007fbf78) */
/* WARNING: Removing unreachable block (ram,0x007fbf7d) */
/* WARNING: Removing unreachable block (ram,0x007fc2de) */
/* WARNING: Removing unreachable block (ram,0x007fc2e3) */
/* WARNING: Removing unreachable block (ram,0x007fc2e8) */
/* WARNING: Removing unreachable block (ram,0x007fc318) */

void FUN_007fbee0(undefined4 param_1,undefined4 param_2)

{
  undefined1 *puVar1;
  int iVar2;
  undefined4 unaff_EDI;
  undefined4 *in_FS_OFFSET;
  bool bVar3;
  int *in_stack_0000000c;
  undefined4 in_stack_00000010;
  int *in_stack_00000014;
  undefined1 local_80 [4];
  undefined1 local_7c [4];
  undefined1 local_78 [4];
  undefined1 local_74 [8];
  undefined1 local_6c [4];
  undefined1 local_68 [12];
  undefined1 local_5c [4];
  undefined1 local_58 [8];
  undefined4 local_50 [2];
  undefined4 local_48 [6];
  undefined4 uStack_30;
  undefined2 uStack_2c;
  undefined2 uStack_2a;
  undefined4 uStack_28;
  undefined1 *local_24;
  undefined1 *puStack_20;
  undefined2 uStack_1c;
  undefined2 uStack_1a;
  undefined4 local_8;
  
  iVar2 = 0xf;
  do {
    iVar2 = iVar2 + -1;
  } while (iVar2 != 0);
  LOCK();
  UNLOCK();
  uStack_1c = (undefined2)unaff_EDI;
  uStack_1a = (undefined2)((uint)unaff_EDI >> 0x10);
  puStack_20 = (undefined1 *)0x7fbf06;
  local_8 = param_2;
  FUN_0040884c(param_2);
  puStack_20 = (undefined1 *)0x7fbf0e;
  FUN_0040884c(in_stack_00000010);
  bVar3 = true;
  local_24 = &LAB_007fc3ca;
  uStack_28 = *in_FS_OFFSET;
  *in_FS_OFFSET = &uStack_28;
  uStack_2c = 0xbf2d;
  uStack_2a = 0x7f;
  puStack_20 = &stack0xfffffffc;
  FUN_00409150(in_stack_00000010,"[matl_alpha]");
  if (bVar3) {
    iVar2 = *in_stack_0000000c;
    *in_stack_0000000c = *in_stack_0000000c + 1;
    if (SCARRY4(iVar2,1)) {
      uStack_2c = 0xbf39;
      uStack_2a = 0x7f;
                    /* WARNING: Subroutine does not return */
      thunk_FUN_00404770();
    }
    uStack_2c = 0xbf46;
    uStack_2a = 0x7f;
    (**(code **)(*in_stack_00000014 + 0xc))(in_stack_00000014,*in_stack_0000000c,local_48);
    uStack_30 = 0x7fbf56;
    FUN_004092cc(&stack0x00000010,local_48[0],0);
  }
  else {
    uStack_2c = 0xbf92;
    uStack_2a = 0x7f;
    FUN_00409150(in_stack_00000010,"[matl_noZwrite]");
    if (!bVar3) {
      uStack_2c = 0xbfb2;
      uStack_2a = 0x7f;
      FUN_00409150(in_stack_00000010,"[matl_noZcheck]");
      if (!bVar3) {
        uStack_2c = 0xbfd2;
        uStack_2a = 0x7f;
        FUN_00409150(in_stack_00000010,"[matl_Zbias]");
        if (bVar3) {
          iVar2 = *in_stack_0000000c;
          *in_stack_0000000c = *in_stack_0000000c + 1;
          if (SCARRY4(iVar2,1)) {
            uStack_2c = 0xbfde;
            uStack_2a = 0x7f;
                    /* WARNING: Subroutine does not return */
            thunk_FUN_00404770();
          }
          uStack_2c = 0xbfeb;
          uStack_2a = 0x7f;
          (**(code **)(*in_stack_00000014 + 0xc))(in_stack_00000014,*in_stack_0000000c,local_50);
          uStack_30 = 0x7fbffb;
          FUN_004092cc(&stack0x00000010,local_50[0],0);
        }
        else {
          uStack_2c = 0xc02b;
          uStack_2a = 0x7f;
          FUN_00409150(in_stack_00000010,"[matl_envmap]");
          if (!bVar3) {
            uStack_2c = 0xc106;
            uStack_2a = 0x7f;
            FUN_00409150(in_stack_00000010,"[matl_envmaprealtime]");
            if (!bVar3) {
              uStack_2c = 0xc175;
              uStack_2a = 0x7f;
              FUN_00409150(in_stack_00000010,"[matl_bumpmap]");
              if (!bVar3) {
                uStack_2c = 0xc24c;
                uStack_2a = 0x7f;
                FUN_00409150(in_stack_00000010,"[matl_envmap_mask]");
                if (!bVar3) {
                  uStack_2c = 0xc2d8;
                  uStack_2a = 0x7f;
                  FUN_00409150(in_stack_00000010,"[matl_transmap]");
                }
              }
            }
          }
        }
      }
    }
  }
  puVar1 = puStack_20;
  *in_FS_OFFSET = uStack_28;
  puStack_20 = &LAB_007fc3d1;
  local_24 = (undefined1 *)0x7fc365;
  FUN_0040877c(local_80,uStack_28,puVar1);
  local_24 = (undefined1 *)0x7fc36d;
  FUN_00408758(local_7c);
  local_24 = (undefined1 *)0x7fc375;
  FUN_0040877c(local_78);
  local_24 = (undefined1 *)0x7fc382;
  FUN_004087b8(local_74,2);
  local_24 = (undefined1 *)0x7fc38a;
  FUN_0040877c(local_6c);
  local_24 = (undefined1 *)0x7fc397;
  FUN_004087b8(local_68,3);
  local_24 = (undefined1 *)0x7fc39f;
  FUN_0040877c(local_5c);
  local_24 = (undefined1 *)0x7fc3ac;
  FUN_004087b8(local_58,5);
  local_24 = (undefined1 *)0x7fc3b9;
  FUN_004087b8(&stack0xffffffec,3);
  local_24 = (undefined1 *)0x7fc3c1;
  FUN_0040877c(&local_8);
  local_24 = (undefined1 *)0x7fc3c9;
  FUN_0040877c(&stack0x00000010);
  return;
}


