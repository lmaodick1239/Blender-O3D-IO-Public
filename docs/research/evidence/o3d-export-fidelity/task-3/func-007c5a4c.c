// 007c5a4c FUN_007c5a4c SHA256 c7765877620816dd4de4cceb21dce1996c8789c89ee550c1fb58440ee689a33e

/* WARNING: Removing unreachable block (ram,0x007c65e5) */

void FUN_007c5a4c(int param_1,int param_2,undefined4 param_3,int param_4)

{
  int iVar1;
  longlong lVar2;
  undefined1 *puVar3;
  char cVar4;
  int iVar5;
  undefined4 uVar6;
  uint uVar7;
  uint uVar8;
  int iVar9;
  undefined4 *puVar10;
  undefined4 *puVar11;
  undefined4 *puVar12;
  undefined4 *puVar13;
  int *in_FS_OFFSET;
  byte bVar14;
  undefined1 *apuStackY_18e8 [1494];
  undefined4 *puStack_188;
  undefined1 *puStack_184;
  uint uStack_180;
  int *piStack_17c;
  int *piStack_178;
  undefined1 *puStack_174;
  int **ppiStack_170;
  int *piStack_16c;
  int *piStack_168;
  undefined4 uStack_164;
  undefined4 uStack_160;
  int *piStack_15c;
  undefined4 *puStack_158;
  int *piStack_154;
  int *piStack_150;
  undefined4 uStack_14c;
  undefined4 uStack_148;
  int *piStack_144;
  uint uStack_140;
  int *piStack_13c;
  undefined4 uStack_138;
  int *piStack_134;
  undefined4 *puStack_130;
  int iStack_12c;
  undefined1 *puStack_128;
  undefined1 *puStack_124;
  undefined4 local_114;
  undefined4 local_110;
  undefined4 local_10c;
  undefined4 auStack_108 [19];
  undefined4 local_bc;
  undefined4 local_b8;
  undefined4 local_b4;
  undefined4 local_b0;
  float local_ac;
  undefined4 local_a8;
  undefined4 local_a4;
  undefined4 local_a0;
  undefined4 local_9c;
  undefined4 local_98;
  undefined4 local_94;
  undefined4 local_90;
  undefined4 local_8c;
  float local_88;
  float local_84;
  float local_80;
  float local_7c;
  float local_78;
  float local_74;
  float local_70;
  float local_6c;
  float local_68;
  float local_64;
  float local_60;
  float local_5c;
  uint local_58;
  float local_54;
  int local_50;
  undefined2 local_4a [3];
  int local_44;
  uint local_40;
  int *local_3c;
  uint local_38;
  float local_34;
  float local_30;
  uint local_28;
  bool local_21;
  int local_20;
  int local_1c;
  int *local_18;
  int *local_14;
  undefined4 local_10;
  int local_c;
  undefined4 local_8;
  
  bVar14 = 0;
  local_110 = 0;
  local_114 = 0;
  local_14 = (int *)0x0;
  local_18 = (int *)0x0;
  local_c = 0;
  local_10 = 0;
  puStack_124 = (undefined1 *)0x7c5a83;
  local_20 = param_2;
  local_1c = param_1;
  local_8 = param_3;
  FUN_0040884c(param_3);
  puStack_128 = &LAB_007c6b4d;
  iStack_12c = *in_FS_OFFSET;
  *in_FS_OFFSET = (int)&iStack_12c;
  puStack_130 = (undefined4 *)0x0;
  piStack_134 = (int *)0x0;
  uStack_138 = 0;
  piStack_13c = (int *)0x7c5aa8;
  puStack_124 = &stack0xfffffffc;
  FUN_005680c8(&local_bc);
  *(undefined4 *)(local_1c + 0x14) = local_bc;
  *(undefined4 *)(local_1c + 0x18) = local_b8;
  *(undefined4 *)(local_1c + 0x1c) = local_b4;
  puStack_130 = (undefined4 *)0x0;
  piStack_134 = (int *)0x0;
  uStack_138 = 0;
  piStack_13c = (int *)0x7c5ad7;
  FUN_005680c8(&local_bc);
  *(undefined4 *)(local_1c + 8) = local_bc;
  *(undefined4 *)(local_1c + 0xc) = local_b8;
  *(undefined4 *)(local_1c + 0x10) = local_b4;
  if (*(int *)(local_20 + 0x68) != -1) {
    puStack_130 = (undefined4 *)0x7c5b09;
    iVar5 = FUN_0040a7fc(*(undefined4 *)(local_20 + 0x60));
    if (iVar5 < 1) {
      if (*(char *)(local_20 + 100) == '\0') {
        puStack_130 = (undefined4 *)0x7c5b73;
        FUN_007c5838(local_1c + 0x135,auStack_108 + 3);
        puStack_130 = &local_b0;
        puVar11 = auStack_108 + 3;
        puVar13 = (undefined4 *)(local_1c + 0xf5);
        for (iVar5 = 0x10; iVar5 != 0; iVar5 = iVar5 + -1) {
          *puVar13 = *puVar11;
          puVar11 = puVar11 + (uint)bVar14 * -2 + 1;
          puVar13 = puVar13 + (uint)bVar14 * -2 + 1;
        }
        *(undefined1 *)(local_1c + 0xf4) = 1;
      }
      else {
        puStack_130 = (undefined4 *)0x7c5b3c;
        FUN_007c58c4(*(undefined4 *)(local_20 + 0x68),local_1c + 0x135,auStack_108 + 3);
        puStack_130 = &local_b0;
        puVar11 = auStack_108 + 3;
        puVar13 = (undefined4 *)(local_1c + 0xf5);
        for (iVar5 = 0x10; iVar5 != 0; iVar5 = iVar5 + -1) {
          *puVar13 = *puVar11;
          puVar11 = puVar11 + (uint)bVar14 * -2 + 1;
          puVar13 = puVar13 + (uint)bVar14 * -2 + 1;
        }
        *(undefined1 *)(local_1c + 0xf4) = 1;
      }
      goto LAB_007c5b95;
    }
  }
  *(undefined1 *)(local_1c + 0xf4) = 0;
LAB_007c5b95:
  puStack_130 = (undefined4 *)0x0;
  piStack_134 = (int *)0x7c5baf;
  FUN_0040a9b0(local_1c + 0x180,&DAT_007c24d0,1);
  puStack_130 = (undefined4 *)0x0;
  piStack_134 = (int *)0x7c5bcc;
  FUN_0040a9b0(local_1c + 0x188,&DAT_007c2558,1);
  local_40 = *(uint *)(local_20 + 0xc);
  if ((int)local_40 < 0) {
                    /* WARNING: Subroutine does not return */
    puStack_130 = (undefined4 *)0x7c5bde;
    thunk_FUN_00404770();
  }
  uVar7 = *(uint *)(local_20 + 8);
  if ((int)uVar7 < 0) {
                    /* WARNING: Subroutine does not return */
    puStack_130 = (undefined4 *)0x7c5bf0;
    thunk_FUN_00404770();
  }
  piStack_144 = (int *)uVar7;
  if (*(char *)(local_20 + 0x10) == '\0') {
    puStack_130 = (undefined4 *)0x7c5c8a;
    puStack_130 = (undefined4 *)FUN_0040c050(local_1c + 0xa0);
    piStack_134 = *(int **)PTR_DAT_00858824;
    uStack_138 = 0x212;
    piStack_13c = (int *)0x220;
    uStack_140 = local_40;
    uStack_148 = 0x7c5ca7;
    uVar6 = D3DXCreateMeshFVF();
    puStack_130 = (undefined4 *)0x7c5cb3;
    FUN_008029ac(uVar6,"O3D Mesh: Create",3);
    puStack_130 = (undefined4 *)0x7c5cbb;
    puStack_130 = (undefined4 *)FUN_0040c050(&local_14);
    piStack_134 = *(int **)(local_1c + 0xa0);
    uStack_138 = 0x7c5ccb;
    uVar6 = (**(code **)(*piStack_134 + 0x34))();
    uStack_138 = 0x7c5cd7;
    FUN_008029ac(uVar6,"O3D Mesh: Get Vertex Buffer",2);
    uStack_138 = 0x7c5cdf;
    uStack_138 = FUN_0040c050(&local_18);
    piStack_13c = *(int **)(local_1c + 0xa0);
    uStack_140 = 0x7c5cef;
    uVar6 = (**(code **)(*piStack_13c + 0x38))();
    uStack_140 = 0x7c5cfb;
    FUN_008029ac(uVar6,"O3D Mesh: Get Index Buffer",2);
  }
  else {
    puStack_130 = (undefined4 *)0x7c5c0a;
    puStack_130 = (undefined4 *)FUN_0040c050(local_1c + 0xa0);
    piStack_134 = *(int **)PTR_DAT_00858824;
    uStack_138 = 0x212;
    piStack_13c = (int *)0x221;
    uStack_140 = local_40;
    uStack_148 = 0x7c5c27;
    uVar6 = D3DXCreateMeshFVF();
    puStack_130 = (undefined4 *)0x7c5c33;
    FUN_008029ac(uVar6,"O3D Mesh: Create",3);
    puStack_130 = (undefined4 *)0x7c5c3b;
    puStack_130 = (undefined4 *)FUN_0040c050(&local_14);
    piStack_134 = *(int **)(local_1c + 0xa0);
    uStack_138 = 0x7c5c4b;
    uVar6 = (**(code **)(*piStack_134 + 0x34))();
    uStack_138 = 0x7c5c57;
    FUN_008029ac(uVar6,"O3D Mesh: Get Vertex Buffer",2);
    uStack_138 = 0x7c5c5f;
    uStack_138 = FUN_0040c050(&local_18);
    piStack_13c = *(int **)(local_1c + 0xa0);
    uStack_140 = 0x7c5c6f;
    uVar6 = (**(code **)(*piStack_13c + 0x38))();
    uStack_140 = 0x7c5c7b;
    FUN_008029ac(uVar6,"O3D Mesh: Get Index Buffer",2);
  }
  uStack_140 = 0;
  piStack_144 = &local_44;
  uStack_148 = (undefined4)((ulonglong)local_40 * 0x28);
  if ((int)((ulonglong)local_40 * 0x28 >> 0x20) != 0) {
                    /* WARNING: Subroutine does not return */
    uStack_148 = 0x7c5d12;
    thunk_FUN_00404770();
  }
  uStack_14c = 0;
  piStack_150 = local_14;
  piStack_154 = (int *)0x7c5d1e;
  iVar5 = (**(code **)(*local_14 + 0x2c))();
  local_21 = iVar5 == 0;
  if (local_40 == 0) {
                    /* WARNING: Subroutine does not return */
    piStack_154 = (int *)0x7c5d34;
    thunk_FUN_00404770();
  }
  if ((int)(local_40 - 1) < 0) {
                    /* WARNING: Subroutine does not return */
    piStack_154 = (int *)0x7c5d3d;
    thunk_FUN_00404770();
  }
  if (-1 < (int)(local_40 - 1)) {
    local_58 = local_40;
    local_28 = 0;
    iVar5 = local_44;
    do {
      iVar9 = *(int *)(local_20 + 0x14);
      if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        piStack_154 = (int *)0x7c5d67;
        thunk_FUN_00404770();
      }
      puVar11 = *(undefined4 **)(iVar9 + local_28 * 4);
      local_b0 = *puVar11;
      local_ac = (float)puVar11[1];
      local_a8 = puVar11[2];
      if (param_4 != 0) {
        piStack_154 = (int *)0x43960000;
        puStack_158 = (undefined4 *)0x0;
        piStack_15c = (undefined4 *)0x0;
        uStack_160 = 0;
        uStack_164 = local_b0;
        piStack_168 = (int *)0x43960000;
        ppiStack_170 = (int **)0x7c5da0;
        piStack_16c = (int *)local_a8;
        FUN_007f0c04(&local_bc);
        uStack_164 = 0x7c5db1;
        cVar4 = FUN_007c41e0(param_4,&local_bc,&local_54);
        if (cVar4 != '\0') {
          local_54 = 300.0 - local_54;
          iVar9 = *(int *)(local_20 + 0x14);
          if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
            uStack_164 = 0x7c5dd9;
            thunk_FUN_00404770();
          }
          local_ac = *(float *)(*(int *)(iVar9 + local_28 * 4) + 4) + local_54;
        }
      }
      iVar9 = *(int *)(local_20 + 0x14);
      if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        piStack_154 = (int *)0x7c5dfd;
        thunk_FUN_00404770();
      }
      local_5c = **(float **)(iVar9 + local_28 * 4);
      local_60 = local_5c;
      if (*(float *)(local_1c + 0x14) < local_5c) {
        local_60 = *(float *)(local_1c + 0x14);
      }
      *(float *)(local_1c + 0x14) = local_60;
      iVar9 = *(int *)(local_20 + 0x14);
      if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        piStack_154 = (int *)0x7c5e45;
        thunk_FUN_00404770();
      }
      local_64 = *(float *)(*(int *)(iVar9 + local_28 * 4) + 4);
      local_68 = local_64;
      if (*(float *)(local_1c + 0x18) < local_64) {
        local_68 = *(float *)(local_1c + 0x18);
      }
      *(float *)(local_1c + 0x18) = local_68;
      iVar9 = *(int *)(local_20 + 0x14);
      if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        piStack_154 = (int *)0x7c5e8e;
        thunk_FUN_00404770();
      }
      local_6c = *(float *)(*(int *)(iVar9 + local_28 * 4) + 8);
      local_70 = local_6c;
      if (*(float *)(local_1c + 0x1c) < local_6c) {
        local_70 = *(float *)(local_1c + 0x1c);
      }
      *(float *)(local_1c + 0x1c) = local_70;
      iVar9 = *(int *)(local_20 + 0x14);
      if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        piStack_154 = (int *)0x7c5ed7;
        thunk_FUN_00404770();
      }
      local_74 = **(float **)(iVar9 + local_28 * 4);
      local_78 = local_74;
      if (local_74 < *(float *)(local_1c + 8)) {
        local_78 = *(float *)(local_1c + 8);
      }
      *(float *)(local_1c + 8) = local_78;
      iVar9 = *(int *)(local_20 + 0x14);
      if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        piStack_154 = (int *)0x7c5f1f;
        thunk_FUN_00404770();
      }
      local_7c = *(float *)(*(int *)(iVar9 + local_28 * 4) + 4);
      local_80 = local_7c;
      if (local_7c < *(float *)(local_1c + 0xc)) {
        local_80 = *(float *)(local_1c + 0xc);
      }
      *(float *)(local_1c + 0xc) = local_80;
      iVar9 = *(int *)(local_20 + 0x14);
      if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        piStack_154 = (int *)0x7c5f68;
        thunk_FUN_00404770();
      }
      local_84 = *(float *)(*(int *)(iVar9 + local_28 * 4) + 8);
      local_88 = local_84;
      if (local_84 < *(float *)(local_1c + 0x10)) {
        local_88 = *(float *)(local_1c + 0x10);
      }
      *(float *)(local_1c + 0x10) = local_88;
      if (*(char *)(local_1c + 0xf4) != '\0') {
        piStack_154 = (int *)(local_1c + 0xf5);
        uStack_160 = 0x7c5fbf;
        piStack_15c = &local_b0;
        puStack_158 = &local_b0;
        D3DXVec3TransformCoord();
      }
      iVar9 = *(int *)(local_20 + 0x14);
      if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        piStack_154 = (int *)0x7c5fd6;
        thunk_FUN_00404770();
      }
      iVar9 = *(int *)(iVar9 + local_28 * 4);
      local_a4 = *(undefined4 *)(iVar9 + 0xc);
      local_a0 = *(undefined4 *)(iVar9 + 0x10);
      local_9c = *(undefined4 *)(iVar9 + 0x14);
      if (*(char *)(local_1c + 0xf4) != '\0') {
        piStack_154 = (int *)(local_1c + 0xf5);
        puStack_158 = &local_a4;
        piStack_15c = &local_a4;
        uStack_160 = 0x7c600d;
        D3DXVec3TransformCoord();
      }
      iVar9 = *(int *)(local_20 + 0x14);
      if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        piStack_154 = (int *)0x7c6024;
        thunk_FUN_00404770();
      }
      iVar9 = *(int *)(iVar9 + local_28 * 4);
      local_98 = *(undefined4 *)(iVar9 + 0x18);
      local_94 = *(undefined4 *)(iVar9 + 0x1c);
      iVar9 = *(int *)(local_20 + 0x14);
      if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        piStack_154 = (int *)0x7c604a;
        thunk_FUN_00404770();
      }
      local_90 = **(undefined4 **)(iVar9 + local_28 * 4);
      iVar9 = *(int *)(local_20 + 0x14);
      if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        piStack_154 = (int *)0x7c6069;
        thunk_FUN_00404770();
      }
      local_8c = *(undefined4 *)(*(int *)(iVar9 + local_28 * 4) + 8);
      piStack_154 = (int *)0x7c6080;
      FUN_004048b4(&local_b0,iVar5,0x28);
      iVar5 = iVar5 + 0x28;
      local_28 = local_28 + 1;
      local_58 = local_58 - 1;
    } while (local_58 != 0);
  }
  piStack_154 = local_14;
  puStack_158 = (undefined4 *)0x7c6098;
  iVar5 = (**(code **)(*local_14 + 0x30))();
  local_21 = iVar5 == 0;
  puStack_158 = (undefined4 *)0x7c60a6;
  FUN_0040c050(&local_14);
  if (*(char *)(local_20 + 0x10) == '\0') {
    puStack_158 = (undefined4 *)0x0;
    piStack_15c = &local_44;
    if ((int)((ulonglong)uVar7 * 2 >> 0x20) != 0) {
                    /* WARNING: Subroutine does not return */
      uStack_160 = 0x7c6191;
      thunk_FUN_00404770();
    }
    lVar2 = ((ulonglong)uVar7 * 2 & 0xffffffff) * 3;
    uStack_160 = (undefined4)lVar2;
    if ((int)((ulonglong)lVar2 >> 0x20) != 0) {
                    /* WARNING: Subroutine does not return */
      uStack_160 = 0x7c619f;
      thunk_FUN_00404770();
    }
    uStack_164 = 0;
    piStack_168 = local_18;
    piStack_16c = (int *)0x7c61ab;
    iVar5 = (**(code **)(*local_18 + 0x2c))();
    local_21 = iVar5 == 0;
    if (uVar7 == 0) {
                    /* WARNING: Subroutine does not return */
      piStack_16c = (int *)0x7c61c0;
      thunk_FUN_00404770();
    }
    if ((int)(uVar7 - 1) < 0) {
                    /* WARNING: Subroutine does not return */
      piStack_16c = (int *)0x7c61c9;
      thunk_FUN_00404770();
    }
    if (-1 < (int)(uVar7 - 1)) {
      local_28 = 0;
      iVar5 = local_44;
      local_58 = uVar7;
      do {
        iVar9 = 1;
        do {
          iVar1 = *(int *)(local_20 + 0x18);
          if ((iVar1 == 0) || (*(uint *)(iVar1 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
            piStack_16c = (int *)0x7c61f4;
            thunk_FUN_00404770();
          }
          if (2 < iVar9 - 1U) {
                    /* WARNING: Subroutine does not return */
            piStack_16c = (int *)0x7c6202;
            thunk_FUN_00404770();
          }
          uVar8 = *(uint *)(*(int *)(iVar1 + local_28 * 4) + -4 + iVar9 * 4);
          if (0xffff < uVar8) {
                    /* WARNING: Subroutine does not return */
            piStack_16c = (int *)0x7c6213;
            thunk_FUN_00404770();
          }
          local_4a[0] = (undefined2)uVar8;
          piStack_16c = (int *)0x7c6226;
          FUN_004048b4(local_4a,iVar5,2);
          iVar5 = iVar5 + 2;
          iVar9 = iVar9 + 1;
        } while (iVar9 != 4);
        local_28 = local_28 + 1;
        local_58 = local_58 - 1;
      } while (local_58 != 0);
    }
    piStack_16c = local_18;
    ppiStack_170 = (int **)0x7c6240;
    iVar5 = (**(code **)(*local_18 + 0x30))();
  }
  else {
    puStack_158 = (undefined4 *)0x0;
    piStack_15c = &local_44;
    if ((int)((ulonglong)uVar7 * 4 >> 0x20) != 0) {
                    /* WARNING: Subroutine does not return */
      uStack_160 = 0x7c60c7;
      thunk_FUN_00404770();
    }
    lVar2 = ((ulonglong)uVar7 * 4 & 0xffffffff) * 3;
    uStack_160 = (undefined4)lVar2;
    if ((int)((ulonglong)lVar2 >> 0x20) != 0) {
                    /* WARNING: Subroutine does not return */
      uStack_160 = 0x7c60d5;
      thunk_FUN_00404770();
    }
    uStack_164 = 0;
    piStack_168 = local_18;
    piStack_16c = (int *)0x7c60e1;
    iVar5 = (**(code **)(*local_18 + 0x2c))();
    local_21 = iVar5 == 0;
    if (uVar7 == 0) {
                    /* WARNING: Subroutine does not return */
      piStack_16c = (int *)0x7c60f6;
      thunk_FUN_00404770();
    }
    if ((int)(uVar7 - 1) < 0) {
                    /* WARNING: Subroutine does not return */
      piStack_16c = (int *)0x7c60ff;
      thunk_FUN_00404770();
    }
    if (-1 < (int)(uVar7 - 1)) {
      local_28 = 0;
      iVar5 = local_44;
      local_58 = uVar7;
      do {
        iVar9 = 1;
        do {
          iVar1 = *(int *)(local_20 + 0x18);
          if ((iVar1 == 0) || (*(uint *)(iVar1 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
            piStack_16c = (int *)0x7c612a;
            thunk_FUN_00404770();
          }
          if (2 < iVar9 - 1U) {
                    /* WARNING: Subroutine does not return */
            piStack_16c = (int *)0x7c6138;
            thunk_FUN_00404770();
          }
          iVar1 = *(int *)(*(int *)(iVar1 + local_28 * 4) + -4 + iVar9 * 4);
          if (iVar1 < 0) {
                    /* WARNING: Subroutine does not return */
            piStack_16c = (int *)0x7c6146;
            thunk_FUN_00404770();
          }
          piStack_16c = (int *)0x7c6158;
          local_50 = iVar1;
          FUN_004048b4(&local_50,iVar5,4);
          iVar5 = iVar5 + 4;
          iVar9 = iVar9 + 1;
        } while (iVar9 != 4);
        local_28 = local_28 + 1;
        local_58 = local_58 - 1;
      } while (local_58 != 0);
    }
    piStack_16c = local_18;
    ppiStack_170 = (int **)0x7c6172;
    iVar5 = (**(code **)(*local_18 + 0x30))();
  }
  local_21 = iVar5 == 0;
  ppiStack_170 = &local_3c;
  puStack_174 = (undefined1 *)0x2000;
  piStack_178 = *(int **)(local_1c + 0xa0);
  piStack_17c = (int *)0x7c625e;
  (**(code **)(*piStack_178 + 0x60))();
  if (uVar7 == 0) {
                    /* WARNING: Subroutine does not return */
    piStack_17c = (int *)0x7c6268;
    thunk_FUN_00404770();
  }
  if ((int)(uVar7 - 1) < 0) {
                    /* WARNING: Subroutine does not return */
    piStack_17c = (int *)0x7c6271;
    thunk_FUN_00404770();
  }
  if (-1 < (int)(uVar7 - 1)) {
    local_28 = 0;
    local_58 = uVar7;
    do {
      iVar5 = *(int *)(local_20 + 0x18);
      if ((iVar5 == 0) || (*(uint *)(iVar5 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        piStack_17c = (int *)0x7c6297;
        thunk_FUN_00404770();
      }
      iVar5 = *(int *)(*(int *)(iVar5 + local_28 * 4) + 0xc);
      if (iVar5 < 0) {
                    /* WARNING: Subroutine does not return */
        piStack_17c = (int *)0x7c62a6;
        thunk_FUN_00404770();
      }
      *local_3c = iVar5;
      local_3c = local_3c + 1;
      local_28 = local_28 + 1;
      local_58 = local_58 - 1;
    } while (local_58 != 0);
  }
  piStack_17c = *(int **)(local_1c + 0xa0);
  uStack_180 = 0x7c62c6;
  (**(code **)(*piStack_17c + 100))();
  uStack_180 = 0x7c62d1;
  uStack_180 = FUN_0040a7fc(*(undefined4 *)(local_20 + 0x1c));
  puStack_184 = (undefined1 *)0x7c62f0;
  local_38 = uStack_180;
  FUN_0040a9b0(local_1c + 0xec,&DAT_007fa9f8,1);
  uStack_180 = local_38;
  puStack_184 = (undefined1 *)0x7c630f;
  FUN_0040a9b0(local_1c + 0xf0,&DAT_007c1dcc,1);
  if (SBORROW4(local_38,1)) {
                    /* WARNING: Subroutine does not return */
    uStack_180 = 0x7c631f;
    thunk_FUN_00404770();
  }
  if (-1 < (int)(local_38 - 1)) {
    local_58 = local_38;
    local_28 = 0;
    do {
      iVar5 = *(int *)(local_1c + 0xec);
      if ((iVar5 == 0) || (*(uint *)(iVar5 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        uStack_180 = 0x7c634c;
        thunk_FUN_00404770();
      }
      uStack_180 = 0x7c6363;
      FUN_0040a058(iVar5 + local_28 * 0xbc,PTR_DAT_008590dc,&DAT_007fa590);
      iVar5 = *(int *)(local_20 + 0x1c);
      if ((iVar5 == 0) || (*(uint *)(iVar5 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        uStack_180 = 0x7c637d;
        thunk_FUN_00404770();
      }
      uStack_180 = 0x7c6390;
      FUN_00408c1c(&local_c,*(undefined4 *)(iVar5 + 0x34 + local_28 * 0x38));
      iVar5 = *(int *)(local_1c + 0xf0);
      if ((iVar5 == 0) || (*(uint *)(iVar5 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        uStack_180 = 0x7c63aa;
        thunk_FUN_00404770();
      }
      uStack_180 = 0x7c63b5;
      FUN_00408bd4(iVar5 + local_28 * 4,local_c);
      uStack_180 = local_28;
      puStack_184 = (undefined1 *)0x7c63c7;
      FUN_007c5670(local_1c,local_8,local_c);
      iVar5 = *(int *)(local_20 + 0x1c);
      if ((iVar5 == 0) || (*(uint *)(iVar5 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        puStack_184 = (undefined1 *)0x7c63de;
        thunk_FUN_00404770();
      }
      iVar9 = *(int *)(local_1c + 0xec);
      if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        puStack_184 = (undefined1 *)0x7c6402;
        thunk_FUN_00404770();
      }
      puVar11 = (undefined4 *)(iVar5 + local_28 * 0x38);
      puVar13 = (undefined4 *)(iVar9 + 0x6c + local_28 * 0xbc);
      puVar12 = puVar13 + (uint)bVar14 * -2 + 1;
      puVar10 = puVar11 + (uint)bVar14 * -2 + 1;
      *puVar13 = *puVar11;
      *puVar12 = *puVar10;
      puVar12[(uint)bVar14 * -2 + 1] = puVar10[(uint)bVar14 * -2 + 1];
      (puVar12 + (uint)bVar14 * -2 + 1)[(uint)bVar14 * -2 + 1] =
           (puVar10 + (uint)bVar14 * -2 + 1)[(uint)bVar14 * -2 + 1];
      puStack_184 = (undefined1 *)0x3f800000;
      puStack_188 = (undefined4 *)0x3f800000;
      FUN_007f3d5c(&local_10c,iVar5,local_28 * 0x2f,0x3f800000,0x3f800000);
      iVar5 = *(int *)(local_1c + 0xec);
      if ((iVar5 == 0) || (*(uint *)(iVar5 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        puStack_184 = (undefined1 *)0x7c6449;
        thunk_FUN_00404770();
      }
      puVar11 = (undefined4 *)(iVar5 + 0x7c + local_28 * 0xbc);
      puVar13 = puVar11 + (uint)bVar14 * -2 + 1;
      *puVar11 = local_10c;
      *puVar13 = auStack_108[(uint)bVar14 * -2];
      puVar13[(uint)bVar14 * -2 + 1] = auStack_108[(uint)bVar14 * -2 + (uint)bVar14 * -2 + 1];
      (puVar13 + (uint)bVar14 * -2 + 1)[(uint)bVar14 * -2 + 1] =
           (auStack_108 + (uint)bVar14 * -2 + (uint)bVar14 * -2 + 1)[(uint)bVar14 * -2 + 1];
      iVar5 = *(int *)(local_20 + 0x1c);
      if ((iVar5 == 0) || (*(uint *)(iVar5 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        puStack_184 = (undefined1 *)0x7c6471;
        thunk_FUN_00404770();
      }
      iVar9 = *(int *)(local_1c + 0xec);
      if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        puStack_184 = (undefined1 *)0x7c6495;
        thunk_FUN_00404770();
      }
      puVar11 = (undefined4 *)(iVar5 + 0x10 + local_28 * 0x38);
      puVar13 = (undefined4 *)(iVar9 + 0x8c + local_28 * 0xbc);
      puVar12 = puVar13 + (uint)bVar14 * -2 + 1;
      puVar10 = puVar11 + (uint)bVar14 * -2 + 1;
      *puVar13 = *puVar11;
      *puVar12 = *puVar10;
      puVar12[(uint)bVar14 * -2 + 1] = puVar10[(uint)bVar14 * -2 + 1];
      (puVar12 + (uint)bVar14 * -2 + 1)[(uint)bVar14 * -2 + 1] =
           (puVar10 + (uint)bVar14 * -2 + 1)[(uint)bVar14 * -2 + 1];
      iVar5 = *(int *)(local_20 + 0x1c);
      if ((iVar5 == 0) || (*(uint *)(iVar5 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        puStack_184 = (undefined1 *)0x7c64be;
        thunk_FUN_00404770();
      }
      iVar9 = *(int *)(local_1c + 0xec);
      if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        puStack_184 = (undefined1 *)0x7c64e2;
        thunk_FUN_00404770();
      }
      puVar11 = (undefined4 *)(iVar5 + 0x20 + local_28 * 0x38);
      puVar13 = (undefined4 *)(iVar9 + 0x9c + local_28 * 0xbc);
      puVar12 = puVar13 + (uint)bVar14 * -2 + 1;
      puVar10 = puVar11 + (uint)bVar14 * -2 + 1;
      *puVar13 = *puVar11;
      *puVar12 = *puVar10;
      puVar12[(uint)bVar14 * -2 + 1] = puVar10[(uint)bVar14 * -2 + 1];
      (puVar12 + (uint)bVar14 * -2 + 1)[(uint)bVar14 * -2 + 1] =
           (puVar10 + (uint)bVar14 * -2 + 1)[(uint)bVar14 * -2 + 1];
      iVar5 = *(int *)(local_20 + 0x1c);
      if ((iVar5 == 0) || (*(uint *)(iVar5 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        puStack_184 = (undefined1 *)0x7c650b;
        thunk_FUN_00404770();
      }
      iVar9 = *(int *)(local_1c + 0xec);
      if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        puStack_184 = (undefined1 *)0x7c6533;
        thunk_FUN_00404770();
      }
      *(undefined4 *)(iVar9 + 0xac + local_28 * 0xbc) =
           *(undefined4 *)(iVar5 + 0x30 + local_28 * 0x38);
      puStack_184 = (undefined1 *)0x0;
      iVar5 = *(int *)(local_1c + 0xec);
      if ((iVar5 == 0) || (*(uint *)(iVar5 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
        puStack_188 = (undefined4 *)0x7c6559;
        thunk_FUN_00404770();
      }
      puStack_188 = (undefined4 *)0x7c6573;
      FUN_0040a9b0(iVar5 + 0xb0 + local_28 * 0xbc,&DAT_007fa558,1);
      puStack_188 = (undefined4 *)*in_FS_OFFSET;
      *in_FS_OFFSET = (int)&stack0xfffffe78;
      puStack_184 = &stack0xfffffffc;
      iVar5 = FUN_007eec30(local_c,"reflexion");
      uVar6 = 0x7c65a0;
      iVar9 = FUN_007eec30(local_c,&DAT_007c6bfc);
      if (iVar5 == 1) {
        iVar5 = 0;
        if (local_c != 0) {
          iVar5 = *(int *)(local_c + -4);
        }
        if (SBORROW4(iVar5,3)) {
                    /* WARNING: Subroutine does not return */
          thunk_FUN_00404770();
        }
        if (iVar9 == iVar5 + -3) {
          puStack_188 = &local_114;
          if (SBORROW4(iVar9,1)) {
                    /* WARNING: Subroutine does not return */
            thunk_FUN_00404770();
          }
          FUN_007f6180(local_c,10,iVar9 + -1,uVar6);
          FUN_004095f4(&local_110,local_114);
          uVar7 = FUN_0042237c(local_110);
          if (0xff < uVar7) {
                    /* WARNING: Subroutine does not return */
            thunk_FUN_00404770();
          }
          iVar5 = *(int *)(local_1c + 0xec);
          if ((iVar5 == 0) || (*(uint *)(iVar5 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
            thunk_FUN_00404770();
          }
          *(char *)(iVar5 + 0x31 + local_28 * 0xbc) = (char)uVar7;
          iVar5 = *(int *)(local_1c + 0xec);
          if ((iVar5 == 0) || (*(uint *)(iVar5 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
            thunk_FUN_00404770();
          }
          *(undefined1 *)(iVar5 + 9 + local_28 * 0xbc) = 1;
        }
      }
      *in_FS_OFFSET = (int)puStack_188;
      local_28 = local_28 + 1;
      local_58 = local_58 - 1;
    } while (local_58 != 0);
  }
  if (param_4 != 0) {
    uStack_180 = 0;
    puStack_184 = *(undefined1 **)(local_1c + 0xa0);
    puStack_188 = (undefined4 *)0x7c6694;
    uVar6 = D3DXComputeNormals();
    uStack_180 = 0x7c66a0;
    FUN_008029ac(uVar6,"Spline Mesh: Compute Normals",2);
  }
  puVar11 = (undefined4 *)(local_20 + 0x20);
  puVar13 = (undefined4 *)(local_1c + 0x60);
  for (iVar5 = 0x10; iVar5 != 0; iVar5 = iVar5 + -1) {
    *puVar13 = *puVar11;
    puVar11 = puVar11 + (uint)bVar14 * -2 + 1;
    puVar13 = puVar13 + (uint)bVar14 * -2 + 1;
  }
  uStack_180 = 0x7c66be;
  iVar5 = FUN_0040a7fc(*(undefined4 *)(local_20 + 0x60));
  if (0 < iVar5) {
    uStack_180 = 0x7c66d1;
    uStack_180 = FUN_0040a7fc(*(undefined4 *)(local_20 + 0x60));
    puStack_184 = (undefined1 *)0x7c66ea;
    FUN_0040a9b0(local_1c + 0x188,&DAT_007c2558,1);
    uStack_180 = 0x7c66fb;
    iVar5 = FUN_0040a804(*(undefined4 *)(local_1c + 0x188));
    if (-1 < iVar5) {
      local_58 = iVar5 + 1;
      local_28 = 0;
      do {
        iVar5 = *(int *)(local_1c + 0x188);
        if ((iVar5 == 0) || (*(uint *)(iVar5 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
          uStack_180 = 0x7c6724;
          thunk_FUN_00404770();
        }
        iVar9 = *(int *)(local_20 + 0x60);
        if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
          uStack_180 = 0x7c673e;
          thunk_FUN_00404770();
        }
        uStack_180 = 0x7c6749;
        FUN_00408bd4(iVar5 + local_28 * 4,*(undefined4 *)(iVar9 + local_28 * 0xc));
        local_28 = local_28 + 1;
        local_58 = local_58 - 1;
      } while (local_58 != 0);
    }
    uStack_180 = local_40;
    puStack_184 = (undefined1 *)0x7c676d;
    FUN_0040a9b0(local_1c + 0x180,&DAT_007c24d0,1);
    uStack_180 = local_40;
    puStack_184 = (undefined1 *)0x7c678c;
    FUN_0040a9b0(local_1c + 0x184,&DAT_007c2514,1);
    uStack_180 = 0x7c679d;
    iVar5 = FUN_0040a804(*(undefined4 *)(local_1c + 0x180));
    if (-1 < iVar5) {
      local_58 = iVar5 + 1;
      local_28 = 0;
      do {
        uStack_180 = 0x7c67bb;
        uStack_180 = FUN_0040a7fc(*(undefined4 *)(local_20 + 0x60));
        iVar5 = *(int *)(local_1c + 0x180);
        if ((iVar5 == 0) || (*(uint *)(iVar5 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
          puStack_184 = (undefined1 *)0x7c67d6;
          thunk_FUN_00404770();
        }
        puStack_184 = (undefined1 *)0x7c67e9;
        FUN_0040a9b0(iVar5 + local_28 * 4,&DAT_007c2454,1);
        uStack_180 = 0x7c67f7;
        iVar5 = FUN_0040a804(*(undefined4 *)(local_20 + 0x60));
        if (-1 < iVar5) {
          iVar5 = iVar5 + 1;
          uVar7 = 0;
          do {
            iVar9 = *(int *)(local_1c + 0x180);
            if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
              uStack_180 = 0x7c681e;
              thunk_FUN_00404770();
            }
            iVar9 = *(int *)(iVar9 + local_28 * 4);
            if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= uVar7)) {
                    /* WARNING: Subroutine does not return */
              uStack_180 = 0x7c682f;
              thunk_FUN_00404770();
            }
            *(undefined4 *)(iVar9 + uVar7 * 4) = 0;
            iVar9 = *(int *)(local_20 + 0x60);
            if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= uVar7)) {
                    /* WARNING: Subroutine does not return */
              uStack_180 = 0x7c6848;
              thunk_FUN_00404770();
            }
            uStack_180 = 0x7c6854;
            iVar9 = FUN_0040a804(*(undefined4 *)(iVar9 + 4 + uVar7 * 0xc));
            if (-1 < iVar9) {
              iVar9 = iVar9 + 1;
              uVar8 = 0;
              do {
                iVar1 = *(int *)(local_20 + 0x60);
                if ((iVar1 == 0) || (*(uint *)(iVar1 + -4) <= uVar7)) {
                    /* WARNING: Subroutine does not return */
                  uStack_180 = 0x7c6875;
                  thunk_FUN_00404770();
                }
                iVar1 = *(int *)(iVar1 + 4 + uVar7 * 0xc);
                if ((iVar1 == 0) || (*(uint *)(iVar1 + -4) <= uVar8)) {
                    /* WARNING: Subroutine does not return */
                  uStack_180 = 0x7c688a;
                  thunk_FUN_00404770();
                }
                if (*(ushort *)(iVar1 + uVar8 * 2) == local_28) {
                  iVar9 = *(int *)(local_20 + 0x60);
                  if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= uVar7)) {
                    /* WARNING: Subroutine does not return */
                    uStack_180 = 0x7c68a7;
                    thunk_FUN_00404770();
                  }
                  iVar9 = *(int *)(iVar9 + 8 + uVar7 * 0xc);
                  if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= uVar8)) {
                    /* WARNING: Subroutine does not return */
                    uStack_180 = 0x7c68bc;
                    thunk_FUN_00404770();
                  }
                  iVar1 = *(int *)(local_1c + 0x180);
                  if ((iVar1 == 0) || (*(uint *)(iVar1 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
                    uStack_180 = 0x7c68d9;
                    thunk_FUN_00404770();
                  }
                  iVar1 = *(int *)(iVar1 + local_28 * 4);
                  if ((iVar1 == 0) || (*(uint *)(iVar1 + -4) <= uVar7)) {
                    /* WARNING: Subroutine does not return */
                    uStack_180 = 0x7c68ea;
                    thunk_FUN_00404770();
                  }
                  *(undefined4 *)(iVar1 + uVar7 * 4) = *(undefined4 *)(iVar9 + uVar8 * 4);
                  break;
                }
                uVar8 = uVar8 + 1;
                iVar9 = iVar9 + -1;
              } while (iVar9 != 0);
            }
            uVar7 = uVar7 + 1;
            iVar5 = iVar5 + -1;
          } while (iVar5 != 0);
        }
        local_30 = 0.0;
        iVar5 = *(int *)(local_1c + 0x180);
        if ((iVar5 == 0) || (*(uint *)(iVar5 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
          uStack_180 = 0x7c691e;
          thunk_FUN_00404770();
        }
        uStack_180 = 0x7c6926;
        iVar5 = FUN_0040a804(*(undefined4 *)(iVar5 + local_28 * 4));
        if (-1 < iVar5) {
          iVar5 = iVar5 + 1;
          uVar7 = 0;
          do {
            iVar9 = *(int *)(local_1c + 0x180);
            if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
              uStack_180 = 0x7c694c;
              thunk_FUN_00404770();
            }
            iVar9 = *(int *)(iVar9 + local_28 * 4);
            if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= uVar7)) {
                    /* WARNING: Subroutine does not return */
              uStack_180 = 0x7c695d;
              thunk_FUN_00404770();
            }
            local_30 = local_30 + *(float *)(iVar9 + uVar7 * 4);
            uVar7 = uVar7 + 1;
            iVar5 = iVar5 + -1;
          } while (iVar5 != 0);
        }
        if (local_30 == 0.0) {
          uStack_180 = 0;
          iVar5 = *(int *)(local_1c + 0x180);
          if ((iVar5 == 0) || (*(uint *)(iVar5 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
            puStack_184 = (undefined1 *)0x7c6993;
            thunk_FUN_00404770();
          }
          puStack_184 = (undefined1 *)0x7c69a6;
          FUN_0040a9b0(iVar5 + local_28 * 4,&DAT_007c2454,1);
          iVar5 = *(int *)(local_1c + 0x184);
          if ((iVar5 == 0) || (*(uint *)(iVar5 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
            uStack_180 = 0x7c69c3;
            thunk_FUN_00404770();
          }
          *(undefined1 *)(iVar5 + local_28) = 0xff;
        }
        local_34 = -1.0;
        iVar5 = *(int *)(local_1c + 0x180);
        if ((iVar5 == 0) || (*(uint *)(iVar5 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
          uStack_180 = 0x7c69e8;
          thunk_FUN_00404770();
        }
        uStack_180 = 0x7c69f0;
        iVar5 = FUN_0040a804(*(undefined4 *)(iVar5 + local_28 * 4));
        if (-1 < iVar5) {
          iVar5 = iVar5 + 1;
          uVar7 = 0;
          do {
            iVar9 = *(int *)(local_1c + 0x180);
            if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
              uStack_180 = 0x7c6a17;
              thunk_FUN_00404770();
            }
            iVar9 = *(int *)(iVar9 + local_28 * 4);
            if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= uVar7)) {
                    /* WARNING: Subroutine does not return */
              uStack_180 = 0x7c6a28;
              thunk_FUN_00404770();
            }
            iVar1 = *(int *)(local_1c + 0x180);
            if ((iVar1 == 0) || (*(uint *)(iVar1 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
              uStack_180 = 0x7c6a48;
              thunk_FUN_00404770();
            }
            iVar1 = *(int *)(iVar1 + local_28 * 4);
            if ((iVar1 == 0) || (*(uint *)(iVar1 + -4) <= uVar7)) {
                    /* WARNING: Subroutine does not return */
              uStack_180 = 0x7c6a59;
              thunk_FUN_00404770();
            }
            *(float *)(iVar1 + uVar7 * 4) = *(float *)(iVar9 + uVar7 * 4) / local_30;
            iVar9 = *(int *)(local_1c + 0x180);
            if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
              uStack_180 = 0x7c6a77;
              thunk_FUN_00404770();
            }
            iVar9 = *(int *)(iVar9 + local_28 * 4);
            if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= uVar7)) {
                    /* WARNING: Subroutine does not return */
              uStack_180 = 0x7c6a88;
              thunk_FUN_00404770();
            }
            if (local_34 < *(float *)(iVar9 + uVar7 * 4)) {
              iVar9 = *(int *)(local_1c + 0x184);
              if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
                uStack_180 = 0x7c6aae;
                thunk_FUN_00404770();
              }
              if (0xff < uVar7 + 0x80) {
                    /* WARNING: Subroutine does not return */
                uStack_180 = 0x7c6ac1;
                thunk_FUN_00404770();
              }
              *(char *)(iVar9 + local_28) = (char)uVar7;
              iVar9 = *(int *)(local_1c + 0x180);
              if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= local_28)) {
                    /* WARNING: Subroutine does not return */
                uStack_180 = 0x7c6ae1;
                thunk_FUN_00404770();
              }
              iVar9 = *(int *)(iVar9 + local_28 * 4);
              if ((iVar9 == 0) || (*(uint *)(iVar9 + -4) <= uVar7)) {
                    /* WARNING: Subroutine does not return */
                uStack_180 = 0x7c6af2;
                thunk_FUN_00404770();
              }
              local_34 = *(float *)(iVar9 + uVar7 * 4);
            }
            uVar7 = uVar7 + 1;
            iVar5 = iVar5 + -1;
          } while (iVar5 != 0);
        }
        local_28 = local_28 + 1;
        local_58 = local_58 - 1;
      } while (local_58 != 0);
    }
  }
  puVar3 = puStack_174;
  *in_FS_OFFSET = (int)piStack_17c;
  puStack_174 = &LAB_007c6b54;
  piStack_178 = (int *)0x7c6b24;
  FUN_0040877c(&local_114,piStack_17c,puVar3);
  piStack_178 = (int *)0x7c6b2f;
  FUN_00408758(&local_110);
  piStack_178 = (int *)0x7c6b37;
  FUN_0040c050(&local_18);
  piStack_178 = (int *)0x7c6b3f;
  FUN_0040c050(&local_14);
  piStack_178 = (int *)0x7c6b4c;
  FUN_004087e8(&local_10,3);
  return;
}


