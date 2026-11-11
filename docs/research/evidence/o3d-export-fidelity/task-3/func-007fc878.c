// 007fc878 FUN_007fc878 SHA256 c7765877620816dd4de4cceb21dce1996c8789c89ee550c1fb58440ee689a33e

/* WARNING: Removing unreachable block (ram,0x007fcb72) */
/* WARNING: Removing unreachable block (ram,0x007fcad9) */

void FUN_007fc878(undefined4 param_1,undefined4 *param_2,byte param_3)

{
  uint uVar1;
  int iVar2;
  int extraout_EDX;
  int extraout_EDX_00;
  undefined4 *puVar3;
  undefined4 *puVar4;
  undefined4 *in_FS_OFFSET;
  byte bVar5;
  undefined1 *puVar6;
  uint uVar7;
  undefined4 uStack_17c;
  undefined1 *puStack_178;
  undefined1 *puStack_174;
  undefined1 local_164 [64];
  undefined4 local_124 [5];
  undefined4 local_110;
  undefined4 local_104;
  undefined4 local_100;
  int local_e4;
  int local_e0;
  int local_dc;
  int local_d8;
  int local_d4;
  int local_d0;
  int local_cc;
  int local_c8;
  undefined4 local_c0 [47];
  
  bVar5 = 0;
  puVar3 = local_c0;
  for (iVar2 = 0x2f; iVar2 != 0; iVar2 = iVar2 + -1) {
    *puVar3 = *param_2;
    param_2 = param_2 + 1;
    puVar3 = puVar3 + 1;
  }
  puStack_174 = (undefined1 *)0x7fc8aa;
  FUN_00409f30(local_c0,&DAT_007fa590);
  puStack_178 = &LAB_007fcbf7;
  uStack_17c = *in_FS_OFFSET;
  *in_FS_OFFSET = &uStack_17c;
  puStack_174 = &stack0xfffffffc;
  if (*PTR_DAT_00859e08 == '\0') {
    puStack_174 = &stack0xfffffffc;
    FUN_00800d80(DAT_00861ca8,0x37,3);
    FUN_00800d10(DAT_00861ca8,0,2,2);
    FUN_00800d10(DAT_00861ca8,0,3,0);
    FUN_00800d10(DAT_00861ca8,0,1,4);
    FUN_00800d10(DAT_00861ca8,0,5,2);
    FUN_00800d10(DAT_00861ca8,0,4,2);
    FUN_00800d10(DAT_00861ca8,1,1,1);
    FUN_00800d10(DAT_00861ca8,1,4,1);
    FUN_00800d80(DAT_00861ca8,0xe,0);
    FUN_00800d80(DAT_00861ca8,7,1);
    FUN_00800d80(DAT_00861ca8,0x1b,1);
    FUN_00800d80(DAT_00861ca8,0x13,1);
    FUN_00800d80(DAT_00861ca8,0x14,2);
    if (SCARRY4((uint)param_3,2)) {
                    /* WARNING: Subroutine does not return */
      thunk_FUN_00404770();
    }
    FUN_00800d80(DAT_00861ca8,0x39,param_3 + 2);
    puVar3 = (undefined4 *)PTR_DAT_00859954;
    puVar4 = local_124;
    for (iVar2 = 0x10; iVar2 != 0; iVar2 = iVar2 + -1) {
      *puVar4 = *puVar3;
      puVar3 = puVar3 + (uint)bVar5 * -2 + 1;
      puVar4 = puVar4 + (uint)bVar5 * -2 + 1;
    }
    local_124[0] = 0x3c5a740e;
    local_110 = 0xbc5a740e;
    local_104 = 0x3eaaaaab;
    local_100 = 0x3f2aaaab;
    FUN_007f0f60(DAT_00861bdc,local_164,0,local_124);
    puVar6 = local_164;
    puVar3 = local_124;
    D3DXMatrixMultiply();
    FUN_007fc500(param_1,local_c0,*(undefined4 *)PTR_DAT_00859e04,0,0,puVar3,puVar6);
    (**(code **)(**(int **)PTR_DAT_00858824 + 0xb0))();
    FUN_00800d10(DAT_00861ca8,0,0xb,1);
    FUN_00800d10(DAT_00861ca8,0,0x18,2);
    FUN_00800d80(DAT_00861ca8,0xf,1);
    if (param_3 == 0) {
      iVar2 = 0;
      uVar7 = 0xff;
      uVar1 = FUN_00404c7c();
      local_cc = uVar7 - uVar1;
      local_c8 = (iVar2 - extraout_EDX) - (uint)(uVar7 < uVar1);
      local_d4 = local_cc;
      local_d0 = local_c8;
      if ((local_c8 != 0) && (local_c8 < 0)) {
        local_d4 = 0;
        local_d0 = 0;
      }
      if (local_d0 != 0) {
                    /* WARNING: Subroutine does not return */
        thunk_FUN_00404770();
      }
      FUN_00800d80(DAT_00861ca8,0x18,local_d4);
    }
    else if (param_3 == 1) {
      iVar2 = 0;
      uVar7 = 0xff;
      uVar1 = FUN_00404c7c();
      local_dc = uVar7 - uVar1;
      local_d8 = (iVar2 - extraout_EDX_00) - (uint)(uVar7 < uVar1);
      local_e4 = local_dc;
      local_e0 = local_d8;
      if ((local_d8 != 0) && (local_d8 < 0)) {
        local_e4 = 0;
        local_e0 = 0;
      }
      if (local_e0 != 0) {
                    /* WARNING: Subroutine does not return */
        thunk_FUN_00404770();
      }
      FUN_00800d80(DAT_00861ca8,0x18,local_e4);
    }
    FUN_00800d80(DAT_00861ca8,0x19,7);
  }
  puVar6 = puStack_174;
  *in_FS_OFFSET = uStack_17c;
  puStack_174 = &LAB_007fcbfe;
  puStack_178 = (undefined1 *)0x7fcbf6;
  FUN_00409dc4(local_c0,&DAT_007fa590,puVar6);
  return;
}


