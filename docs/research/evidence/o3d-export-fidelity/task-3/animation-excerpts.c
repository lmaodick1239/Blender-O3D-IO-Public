// Bounded evidence excerpt; not compilable source. Original: .superpowers/sdd/2026-11-10-o3d-export-fidelity/native-authorized-consumers/func-005fc664.c
// Original SHA256 ef05f4f2677e3e88f441571948d6105f0c166da096daa6527042c28619b436dc; original bytes 26651
// Source line ranges (inclusive): [(1, 12), (72, 159), (340, 461)]

// BEGIN original lines 1..12
// 005fc664 FUN_005fc664 SHA256 c7765877620816dd4de4cceb21dce1996c8789c89ee550c1fb58440ee689a33e

void FUN_005fc664(int param_1,undefined4 *param_2,char param_3,float param_4)

{
  int *piVar1;
  int iVar2;
  float *pfVar3;
  float *pfVar4;
  undefined4 *puVar5;
  undefined4 uVar6;
  undefined4 uVar7;
// END original lines 1..12

// BEGIN original lines 72..159
  
  bVar14 = 0;
  puVar5 = local_f4;
  for (iVar8 = 0x10; iVar8 != 0; iVar8 = iVar8 + -1) {
    *puVar5 = *param_2;
    param_2 = param_2 + 1;
    puVar5 = puVar5 + 1;
  }
  local_5 = param_3;
  if ((param_3 != '\x01') && (*(char *)(param_1 + 0x44) == '\0')) {
    FUN_005fbc7c(param_1,0);
  }
  puVar5 = local_f4;
  puVar12 = (undefined4 *)(param_1 + 0x5c);
  for (iVar8 = 0x10; iVar8 != 0; iVar8 = iVar8 + -1) {
    *puVar12 = *puVar5;
    puVar5 = puVar5 + (uint)bVar14 * -2 + 1;
    puVar12 = puVar12 + (uint)bVar14 * -2 + 1;
  }
  if (local_5 != '\x01') {
    iVar8 = *(int *)(*(int *)(*(int *)(param_1 + 0x20) + 0x38) + 8);
    if (SBORROW4(iVar8,1)) {
                    /* WARNING: Subroutine does not return */
      thunk_FUN_00404770();
    }
    if (-1 < iVar8 + -1) {
      iVar9 = 0;
      local_14 = iVar8;
      do {
        puVar5 = (undefined4 *)PTR_DAT_00859954;
        puVar12 = local_134;
        for (iVar8 = 0x10; iVar8 != 0; iVar8 = iVar8 + -1) {
          *puVar12 = *puVar5;
          puVar5 = puVar5 + (uint)bVar14 * -2 + 1;
          puVar12 = puVar12 + (uint)bVar14 * -2 + 1;
        }
        iVar8 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar9);
        iVar8 = *(int *)(*(int *)(iVar8 + 0x198) + 0xc);
        if (SBORROW4(iVar8,1)) {
                    /* WARNING: Subroutine does not return */
          thunk_FUN_00404770();
        }
        if (-1 < iVar8 + -1) {
          iVar11 = 0;
          local_18 = iVar8;
          do {
            iVar8 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar9);
            FUN_005fed88(*(undefined4 *)(iVar8 + 0x19c),iVar11,local_1b4);
            puVar20 = local_1b4;
            puVar5 = local_134;
            puVar12 = local_134;
            D3DXMatrixMultiply();
            iVar8 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar9);
            FUN_005ff098(*(undefined4 *)(iVar8 + 0x1a0),iVar11,local_1cc,puVar12,puVar5,puVar20);
            if (local_1c8 == 0.0) {
              puVar5 = (undefined4 *)PTR_DAT_00859954;
              puVar12 = local_174;
              for (iVar8 = 0x10; iVar8 != 0; iVar8 = iVar8 + -1) {
                *puVar12 = *puVar5;
                puVar5 = puVar5 + (uint)bVar14 * -2 + 1;
                puVar12 = puVar12 + (uint)bVar14 * -2 + 1;
              }
            }
            else {
              iVar8 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar9);
              FUN_005ff098(*(undefined4 *)(iVar8 + 0x1a0),iVar11,local_1cc,puVar12,puVar5,puVar20);
              iVar8 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar9);
              FUN_005ff098(*(undefined4 *)(iVar8 + 0x1a0),iVar11,local_1e4);
              iVar8 = **(int **)(param_1 + 0x28);
              if ((iVar8 == 0) || (*(uint *)(iVar8 + -4) <= local_1e4[0])) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              local_1f0 = (float10)**(float **)(iVar8 + local_1e4[0] * 4) * (float10)local_1c8;
              iVar8 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar9);
              FUN_005ff098(*(undefined4 *)(iVar8 + 0x1a0),iVar11,local_208);
              local_c = (float)(local_1f0 + (float10)local_1fc);
              fVar17 = in_ST5;
              iVar8 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar9);
              FUN_005ff098(*(undefined4 *)(iVar8 + 0x1a0),iVar11,local_1cc);
              fVar15 = in_ST1;
              fVar16 = in_ST3;
              if (local_1bc == 0.0) {
                iVar8 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar9);
                FUN_005ff098(*(undefined4 *)(iVar8 + 0x1a0),iVar11,local_1e4);
                fVar15 = in_ST1;
                fVar16 = in_ST3;
                if (local_1d0 != 0.0) goto LAB_005fc8b0;
// END original lines 72..159

// BEGIN original lines 340..461
            puVar5 = puVar5 + (uint)bVar14 * -2 + 1;
            puVar12 = puVar12 + (uint)bVar14 * -2 + 1;
          }
        }
        else {
          FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar9);
          FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar9);
          D3DXMatrixMultiply();
        }
        iVar9 = iVar9 + 1;
        local_14 = local_14 + -1;
      } while (local_14 != 0);
    }
    FUN_005fd650(param_1);
    iVar8 = FUN_0040a804(*(undefined4 *)(param_1 + 0x30));
    if (-1 < iVar8) {
      local_14 = iVar8 + 1;
      uVar10 = 0;
      do {
        iVar8 = *(int *)(param_1 + 0x30);
        if ((iVar8 == 0) || (*(uint *)(iVar8 + -4) <= uVar10)) {
                    /* WARNING: Subroutine does not return */
          thunk_FUN_00404770();
        }
        FUN_007c2d64(*(undefined4 *)(iVar8 + uVar10 * 4));
        uVar10 = uVar10 + 1;
        local_14 = local_14 + -1;
      } while (local_14 != 0);
    }
  }
  iVar8 = *(int *)(*(int *)(*(int *)(param_1 + 0x20) + 0x38) + 8);
  if (SBORROW4(iVar8,1)) {
                    /* WARNING: Subroutine does not return */
    thunk_FUN_00404770();
  }
  if (-1 < iVar8 + -1) {
    iVar9 = 0;
    local_14 = iVar8;
    do {
      if (local_5 == '\0') {
        iVar8 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar9);
        if (*(int *)(iVar8 + 0x1a4) < 0) {
LAB_005fcfa8:
          iVar8 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar9);
          *(undefined1 *)(iVar8 + 0xd0) = 1;
        }
        else {
          iVar8 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar9);
          iVar8 = *(int *)(iVar8 + 0x1a4);
          iVar11 = FUN_0040a804(**(undefined4 **)(param_1 + 0x28));
          if (iVar11 < iVar8) goto LAB_005fcfa8;
          iVar8 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar9);
          if ((**(int **)(param_1 + 0x28) == 0) ||
             (*(uint *)(**(int **)(param_1 + 0x28) + -4) <= *(uint *)(iVar8 + 0x1a4))) {
                    /* WARNING: Subroutine does not return */
            thunk_FUN_00404770();
          }
          iVar11 = FUN_00404c7c();
          iVar8 = extraout_EDX;
          iVar2 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar9);
          uVar13 = *(int *)(iVar2 + 0x1a8) >> 0x1f == iVar8 && *(int *)(iVar2 + 0x1a8) == iVar11;
          iVar8 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar9);
          *(undefined1 *)(iVar8 + 0xd0) = uVar13;
        }
        iVar8 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar9);
        iVar8 = *(int *)(*(int *)(iVar8 + 0xd4) + 8);
        if (SBORROW4(iVar8,1)) {
                    /* WARNING: Subroutine does not return */
          thunk_FUN_00404770();
        }
        if (-1 < iVar8 + -1) {
          iVar11 = 0;
          local_18 = iVar8;
          do {
            iVar8 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar9);
            iVar8 = iVar8 + 8;
            iVar2 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar9);
            iVar2 = FUN_00601990(*(undefined4 *)(iVar2 + 0xd4),iVar11);
            FUN_007f3770(*(int *)(iVar2 + 4) + 0x14,iVar8,&local_214);
            iVar8 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar9);
            iVar8 = FUN_00601990(*(undefined4 *)(iVar8 + 0xd4),iVar11);
            *(undefined4 *)(iVar8 + 0x11) = local_214;
            *(undefined4 *)(iVar8 + 0x15) = local_210;
            *(undefined4 *)(iVar8 + 0x19) = local_20c;
            iVar8 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar9);
            iVar8 = FUN_00601990(*(undefined4 *)(iVar8 + 0xd4),iVar11);
            if (*(char *)(*(int *)(iVar8 + 4) + 0x38) == '\0') {
LAB_005fd0a6:
              iVar8 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar9);
              iVar8 = iVar8 + 8;
              iVar2 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar9);
              iVar2 = FUN_00601990(*(undefined4 *)(iVar2 + 0xd4),iVar11);
              FUN_007f39d8(*(int *)(iVar2 + 4) + 0x20,iVar8,&local_214);
              iVar8 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar9);
              iVar8 = FUN_00601990(*(undefined4 *)(iVar8 + 0xd4),iVar11);
              *(undefined4 *)(iVar8 + 0x1d) = local_214;
              *(undefined4 *)(iVar8 + 0x21) = local_210;
              *(undefined4 *)(iVar8 + 0x25) = local_20c;
              iVar8 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar9);
              iVar8 = iVar8 + 8;
              iVar2 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar9);
              iVar2 = FUN_00601990(*(undefined4 *)(iVar2 + 0xd4),iVar11);
              FUN_007f39d8(*(int *)(iVar2 + 4) + 0x2c,iVar8,&local_214);
              iVar8 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar9);
              iVar8 = FUN_00601990(*(undefined4 *)(iVar8 + 0xd4),iVar11);
              *(undefined4 *)(iVar8 + 0x29) = local_214;
              *(undefined4 *)(iVar8 + 0x2d) = local_210;
              *(undefined4 *)(iVar8 + 0x31) = local_20c;
            }
            else {
              iVar8 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar9);
              iVar8 = FUN_00601990(*(undefined4 *)(iVar8 + 0xd4),iVar11);
              if (*(char *)(*(int *)(iVar8 + 4) + 0x39) == '\0') goto LAB_005fd0a6;
            }
            iVar8 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar9);
            iVar8 = FUN_00601990(*(undefined4 *)(iVar8 + 0xd4),iVar11);
            *(undefined1 *)(iVar8 + 0x10) = 0;
            iVar8 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar9);
            iVar8 = FUN_00601990(*(undefined4 *)(iVar8 + 0xd4),iVar11);
            uVar6 = *(undefined4 *)(*(int *)(iVar8 + 4) + 0x3c);
            iVar8 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar9);
            iVar8 = FUN_00601990(*(undefined4 *)(iVar8 + 0xd4),iVar11);
// END original lines 340..461
