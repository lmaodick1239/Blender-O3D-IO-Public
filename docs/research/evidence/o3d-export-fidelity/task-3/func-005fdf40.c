// 005fdf40 FUN_005fdf40 SHA256 c7765877620816dd4de4cceb21dce1996c8789c89ee550c1fb58440ee689a33e

/* WARNING: Removing unreachable block (ram,0x005fe2a7) */
/* WARNING: Removing unreachable block (ram,0x005fe284) */

void FUN_005fdf40(int param_1)

{
  undefined *puVar1;
  int iVar2;
  int iVar3;
  undefined4 uVar4;
  uint uVar5;
  undefined4 uVar6;
  int iVar7;
  undefined4 *in_FS_OFFSET;
  int *piVar8;
  int *piVar9;
  undefined4 uStack_94;
  undefined1 *puStack_90;
  undefined1 *puStack_8c;
  undefined1 local_7c [76];
  int local_30;
  uint local_2c;
  int local_28;
  undefined4 local_24;
  undefined4 *local_20;
  undefined4 *local_1c;
  undefined4 *local_18;
  undefined4 *local_14;
  uint local_10;
  int *local_c;
  int *local_8;
  
  puStack_8c = &stack0xfffffffc;
  local_8 = (int *)0x0;
  local_c = (int *)0x0;
  puStack_90 = &LAB_005fe53b;
  uStack_94 = *in_FS_OFFSET;
  *in_FS_OFFSET = &uStack_94;
  iVar2 = *(int *)(*(int *)(param_1 + 0xe0) + 8);
  if (SBORROW4(iVar2,1)) {
                    /* WARNING: Subroutine does not return */
    thunk_FUN_00404770();
  }
  if (-1 < iVar2 + -1) {
    iVar7 = 0;
    puStack_8c = &stack0xfffffffc;
    local_28 = iVar2;
    do {
      iVar2 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar7);
      if (((*(char *)(iVar2 + 0xe5) != '\0') &&
          ((((iVar2 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7),
             *(float *)(iVar2 + 0x1c0) == -1.0 ||
             (iVar2 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7),
             *(float *)(param_1 + 0x10) <= *(float *)(iVar2 + 0x1c0))) &&
            (iVar2 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar7),
            *(int *)(iVar2 + 0xe0) != 0)) &&
           (iVar2 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7),
           *(int *)(iVar2 + 0x1c8) == *(int *)(param_1 + 8))))) &&
         ((iVar2 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7),
          (*(byte *)(iVar2 + 0x1d1) & *(byte *)(param_1 + 0x24)) != 0 ||
          (iVar2 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7),
          *(char *)(iVar2 + 0x1d1) == '\0')))) {
        local_24 = FUN_005fef58(&DAT_005dd80c,1);
        iVar2 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7);
        FUN_005fed20(local_24,*(undefined4 *)(*(int *)(iVar2 + 0x1b8) + 0xc));
        iVar2 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7);
        uVar5 = *(uint *)(*(int *)(iVar2 + 0x1b8) + 0xc);
        if (SBORROW4(uVar5,1)) {
                    /* WARNING: Subroutine does not return */
          thunk_FUN_00404770();
        }
        if (-1 < (int)(uVar5 - 1)) {
          iVar2 = 0;
          local_2c = uVar5;
          do {
            iVar3 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7);
            iVar3 = FUN_00601260(*(undefined4 *)(iVar3 + 0x1b8),iVar2);
            if (iVar3 < 0) {
LAB_005fe11e:
              iVar3 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7);
              iVar3 = FUN_00601260(*(undefined4 *)(iVar3 + 0x1b8),iVar2);
              if (SBORROW4(-2,iVar3)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              if (-1 < -2 - iVar3) {
                iVar3 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7);
                iVar3 = FUN_00601260(*(undefined4 *)(iVar3 + 0x1b8),iVar2);
                if (SBORROW4(-2,iVar3)) {
                    /* WARNING: Subroutine does not return */
                  thunk_FUN_00404770();
                }
                if (-2 - iVar3 < *(int *)(*(int *)(param_1 + 0xec) + 0xc)) {
                  iVar3 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7);
                  iVar3 = FUN_00601260(*(undefined4 *)(iVar3 + 0x1b8),iVar2);
                  if (SBORROW4(-2,iVar3)) {
                    /* WARNING: Subroutine does not return */
                    thunk_FUN_00404770();
                  }
                  FUN_005fed88(*(undefined4 *)(param_1 + 0xec),-2 - iVar3,local_7c);
                  FUN_005fedc8(local_24,iVar2,local_7c);
                  goto LAB_005fe1d0;
                }
              }
              FUN_005fedc8(local_24,iVar2,PTR_DAT_00859954);
            }
            else {
              iVar3 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7);
              iVar3 = FUN_00601260(*(undefined4 *)(iVar3 + 0x1b8),iVar2);
              if (*(int *)(*(int *)(*(int *)(param_1 + 0x20) + 0x38) + 8) <= iVar3)
              goto LAB_005fe11e;
              iVar3 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7);
              uVar4 = FUN_00601260(*(undefined4 *)(iVar3 + 0x1b8),iVar2);
              iVar3 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),uVar4);
              FUN_005fedc8(local_24,iVar2,iVar3 + 0x88);
            }
LAB_005fe1d0:
            iVar2 = iVar2 + 1;
            local_2c = local_2c - 1;
          } while (local_2c != 0);
        }
        iVar2 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar7);
        *(undefined1 *)(iVar2 + 0xe4) = 1;
        iVar2 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar7);
        piVar8 = *(int **)(iVar2 + 0xe0);
        uVar5 = (**(code **)(*piVar8 + 0x14))();
        if (0xffff < uVar5) {
                    /* WARNING: Subroutine does not return */
          thunk_FUN_00404770();
        }
        uVar4 = FUN_0040c050(&local_8);
        iVar2 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar7);
        piVar9 = *(int **)(iVar2 + 0xe0);
        uVar6 = (**(code **)(*piVar9 + 0x34))();
        FUN_008029ac(uVar6,"O3D Skinning: Get Vertex Buffer",2,piVar9,uVar4,piVar8);
        uVar4 = FUN_0040c050(&local_c);
        iVar2 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7);
        piVar8 = *(int **)(iVar2 + 0xa0);
        uVar6 = (**(code **)(*piVar8 + 0x34))();
        FUN_008029ac(uVar6,"O3D Skinning: Get Vertex Buffer",2,piVar8,uVar4);
        (**(code **)(*local_8 + 0x2c))();
        (**(code **)(*local_c + 0x2c))();
        local_18 = local_14;
        local_20 = local_1c;
        uVar5 = uVar5 & 0xffff;
        if (SBORROW4(uVar5,1)) {
                    /* WARNING: Subroutine does not return */
          thunk_FUN_00404770();
        }
        if (-1 < (int)(uVar5 - 1)) {
          local_10 = 0;
          local_2c = uVar5;
          do {
            iVar2 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7);
            if (*(char *)(iVar2 + 0x1bc) == '\0') {
              iVar2 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7);
              iVar2 = *(int *)(iVar2 + 0x184);
              if ((iVar2 == 0) || (*(uint *)(iVar2 + -4) <= local_10)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              if (-1 < *(char *)(iVar2 + local_10)) {
                iVar2 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7);
                iVar2 = *(int *)(iVar2 + 0x184);
                if ((iVar2 == 0) || (*(uint *)(iVar2 + -4) <= local_10)) {
                    /* WARNING: Subroutine does not return */
                  thunk_FUN_00404770();
                }
                FUN_005fed88(local_24,(int)*(char *)(iVar2 + local_10),local_7c);
                D3DXVec3TransformCoord();
              }
            }
            else {
              iVar2 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7);
              iVar2 = *(int *)(iVar2 + 0x180);
              if ((iVar2 == 0) || (*(uint *)(iVar2 + -4) <= local_10)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              iVar2 = FUN_0040a7fc(*(undefined4 *)(iVar2 + local_10 * 4));
              puVar1 = PTR_DAT_00858f68;
              if (iVar2 < 1) {
                *local_18 = *local_20;
                local_18[1] = local_20[1];
                local_18[2] = local_20[2];
              }
              else {
                *local_18 = *(undefined4 *)PTR_DAT_00858f68;
                local_18[1] = *(undefined4 *)(puVar1 + 4);
                local_18[2] = *(undefined4 *)(puVar1 + 8);
                iVar2 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7);
                iVar2 = *(int *)(iVar2 + 0x180);
                if ((iVar2 == 0) || (*(uint *)(iVar2 + -4) <= local_10)) {
                    /* WARNING: Subroutine does not return */
                  thunk_FUN_00404770();
                }
                iVar2 = FUN_0040a804(*(undefined4 *)(iVar2 + local_10 * 4));
                if (-1 < iVar2) {
                  local_30 = iVar2 + 1;
                  uVar5 = 0;
                  do {
                    FUN_005fed88(local_24,uVar5,local_7c);
                    D3DXVec3TransformCoord();
                    iVar2 = FUN_0060382c(*(undefined4 *)(*(int *)(param_1 + 0x20) + 0x38),iVar7);
                    iVar2 = *(int *)(iVar2 + 0x180);
                    if ((iVar2 == 0) || (*(uint *)(iVar2 + -4) <= local_10)) {
                    /* WARNING: Subroutine does not return */
                      thunk_FUN_00404770();
                    }
                    iVar2 = *(int *)(iVar2 + local_10 * 4);
                    if ((iVar2 == 0) || (*(uint *)(iVar2 + -4) <= uVar5)) {
                    /* WARNING: Subroutine does not return */
                      thunk_FUN_00404770();
                    }
                    INLD3DXVec3Scale();
                    INLD3DXVec3Add();
                    uVar5 = uVar5 + 1;
                    local_30 = local_30 + -1;
                  } while (local_30 != 0);
                  local_30 = 0;
                }
              }
            }
            local_18 = local_18 + 10;
            local_20 = local_20 + 10;
            local_10 = local_10 + 1;
            local_2c = local_2c - 1;
          } while (local_2c != 0);
        }
        (**(code **)(*local_8 + 0x30))();
        (**(code **)(*local_c + 0x30))();
        FUN_0040c050(&local_8);
        FUN_0040c050(&local_c);
        uVar4 = local_24;
        local_24 = 0;
        FUN_00406b0c(uVar4);
        FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar7);
        D3DXComputeNormals();
        iVar2 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar7);
        *(undefined1 *)(iVar2 + 0xe4) = 0;
        iVar2 = FUN_0060aef8(*(undefined4 *)(param_1 + 0xe0),iVar7);
        *(undefined1 *)(iVar2 + 0xe5) = 0;
      }
      iVar7 = iVar7 + 1;
      local_28 = local_28 + -1;
    } while (local_28 != 0);
  }
  *in_FS_OFFSET = uStack_94;
  puStack_8c = &LAB_005fe542;
  puStack_90 = (undefined1 *)0x5fe53a;
  FUN_00409e14(&local_c,&DAT_00561604,2);
  return;
}


