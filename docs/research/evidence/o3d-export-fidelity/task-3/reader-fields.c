// Bounded evidence excerpt; not compilable source. Original: .superpowers/sdd/2026-11-10-o3d-export-fidelity/native-authorized-seed/func-0056c7b4.c
// Original SHA256 18887b85e8962364614cdb37fb5f04125e91cf669b26b65064db8fac231296e7; original bytes 38274
// Source line ranges (inclusive): [(1, 8), (475, 585), (744, 911), (1000, 1034)]

// BEGIN original lines 1..8
// 0056c7b4 FUN_0056c7b4 SHA256 c7765877620816dd4de4cceb21dce1996c8789c89ee550c1fb58440ee689a33e

/* WARNING: Removing unreachable block (ram,0x0056cc0a) */
/* WARNING: Removing unreachable block (ram,0x0056d3d6) */
/* WARNING: Removing unreachable block (ram,0x0056d380) */

void FUN_0056c7b4(undefined4 param_1,uint *param_2)

// END original lines 1..8

// BEGIN original lines 475..585
            FUN_00404788();
            local_3c = (uint)local_20;
          }
          else {
            FUN_004052a0(local_2f4,&local_3c,4,local_28);
            FUN_00404788();
          }
          if ((int)local_3c < 0) {
                    /* WARNING: Subroutine does not return */
            thunk_FUN_00404770();
          }
          *(uint *)(*local_c + 8) = local_3c;
          FUN_0040a9b0(*local_c + 0x18,&DAT_0056acb8,1,*(undefined4 *)(*local_c + 8));
          if (local_3c == 0) {
                    /* WARNING: Subroutine does not return */
            thunk_FUN_00404770();
          }
          if ((int)(local_3c - 1) < 0) {
                    /* WARNING: Subroutine does not return */
            thunk_FUN_00404770();
          }
          if (-1 < (int)(local_3c - 1)) {
            local_70 = local_3c;
            uVar8 = 0;
            do {
              uVar10 = FUN_00404614(0x10);
              iVar11 = *(int *)(*local_c + 0x18);
              if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar8)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              *(undefined4 *)(iVar11 + uVar8 * 4) = uVar10;
              if (local_45 == false) {
                FUN_004052a0(local_2f4,&local_2e,2,local_28);
                FUN_00404788();
                iVar11 = *(int *)(*local_c + 0x18);
                if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar8)) {
                    /* WARNING: Subroutine does not return */
                  thunk_FUN_00404770();
                }
                **(uint **)(iVar11 + uVar8 * 4) = (uint)local_2e;
                FUN_004052a0(local_2f4,&local_2e,2,local_28);
                FUN_00404788();
                iVar11 = *(int *)(*local_c + 0x18);
                if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar8)) {
                    /* WARNING: Subroutine does not return */
                  thunk_FUN_00404770();
                }
                *(uint *)(*(int *)(iVar11 + uVar8 * 4) + 4) = (uint)local_2e;
                FUN_004052a0(local_2f4,&local_2e,2,local_28);
                FUN_00404788();
                iVar11 = *(int *)(*local_c + 0x18);
                if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar8)) {
                    /* WARNING: Subroutine does not return */
                  thunk_FUN_00404770();
                }
                *(uint *)(*(int *)(iVar11 + uVar8 * 4) + 8) = (uint)local_2e;
              }
              else {
                FUN_004052a0(local_2f4,&local_34,4,local_28);
                FUN_00404788();
                iVar11 = *(int *)(*local_c + 0x18);
                if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar8)) {
                    /* WARNING: Subroutine does not return */
                  thunk_FUN_00404770();
                }
                if (local_34 < 0) {
                    /* WARNING: Subroutine does not return */
                  thunk_FUN_00404770();
                }
                **(int **)(iVar11 + uVar8 * 4) = local_34;
                FUN_004052a0(local_2f4,&local_34,4,local_28);
                FUN_00404788();
                iVar11 = *(int *)(*local_c + 0x18);
                if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar8)) {
                    /* WARNING: Subroutine does not return */
                  thunk_FUN_00404770();
                }
                if (local_34 < 0) {
                    /* WARNING: Subroutine does not return */
                  thunk_FUN_00404770();
                }
                *(int *)(*(int *)(iVar11 + uVar8 * 4) + 4) = local_34;
                FUN_004052a0(local_2f4,&local_34,4,local_28);
                FUN_00404788();
                iVar11 = *(int *)(*local_c + 0x18);
                if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar8)) {
                    /* WARNING: Subroutine does not return */
                  thunk_FUN_00404770();
                }
                if (local_34 < 0) {
                    /* WARNING: Subroutine does not return */
                  thunk_FUN_00404770();
                }
                *(int *)(*(int *)(iVar11 + uVar8 * 4) + 8) = local_34;
              }
              FUN_004052a0(local_2f4,&local_2e,2,local_28);
              FUN_00404788();
              iVar11 = *(int *)(*local_c + 0x18);
              if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar8)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              *(uint *)(*(int *)(iVar11 + uVar8 * 4) + 0xc) = (uint)local_2e;
              uVar8 = uVar8 + 1;
              local_70 = local_70 - 1;
            } while (local_70 != 0);
            local_70 = 0;
          }
        }
        else if (local_19 == 0x17) {
// END original lines 475..585

// BEGIN original lines 744..911
                if ((uint)local_5a % 5 == 0) {
                  local_34c = (int)((ulonglong)((uint)local_5a % 100) * ((ulonglong)local_5a % 100))
                  ;
                  local_68 = (float)local_34c / 10000.0;
                  local_54 = local_54 - local_68;
                }
                if ((uint)local_5a % 3 == 0) {
                  local_34c = (int)((ulonglong)((uint)local_5a % 0x32) *
                                   ((ulonglong)local_5a % 0x32));
                  local_68 = (float)local_34c / 2500.0;
                  local_50 = local_50 - local_68;
                }
              }
              iVar11 = *(int *)(*local_c + 0x14);
              if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar8)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              pfVar1 = *(float **)(iVar11 + uVar8 * 4);
              *pfVar1 = local_300;
              pfVar1[1] = local_2fc;
              pfVar1[2] = local_2f8;
              iVar11 = *(int *)(*local_c + 0x14);
              if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar8)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              iVar11 = *(int *)(iVar11 + uVar8 * 4);
              *(float *)(iVar11 + 0xc) = local_30c;
              *(float *)(iVar11 + 0x10) = local_308;
              *(float *)(iVar11 + 0x14) = local_304;
              iVar11 = *(int *)(*local_c + 0x14);
              if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar8)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              iVar11 = *(int *)(iVar11 + uVar8 * 4);
              *(float *)(iVar11 + 0x18) = local_54;
              *(float *)(iVar11 + 0x1c) = local_50;
              uVar8 = uVar8 + 1;
              local_70 = local_70 - 1;
            } while (local_70 != 0);
            local_70 = 0;
          }
        }
        else if (local_19 == 0x26) {
          FUN_004052a0(local_2f4,&local_20,2,local_28);
          FUN_00404788();
          FUN_0040a9b0(*local_c + 0x1c,&DAT_0056acf0,1,local_20);
          uVar8 = (uint)local_20;
          if (SBORROW4(uVar8,1)) {
                    /* WARNING: Subroutine does not return */
            thunk_FUN_00404770();
          }
          if (-1 < (int)(uVar8 - 1)) {
            uVar13 = 0;
            local_70 = uVar8;
            do {
              FUN_004052a0(local_2f4,&local_2c,4,local_28);
              FUN_00404788();
              iVar11 = *(int *)(*local_c + 0x1c);
              if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar13)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              *(float *)(iVar11 + uVar13 * 0x38) = local_2c;
              FUN_004052a0(local_2f4,&local_2c,4,local_28);
              FUN_00404788();
              iVar11 = *(int *)(*local_c + 0x1c);
              if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar13)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              *(float *)(iVar11 + 4 + uVar13 * 0x38) = local_2c;
              FUN_004052a0(local_2f4,&local_2c,4,local_28);
              FUN_00404788();
              iVar11 = *(int *)(*local_c + 0x1c);
              if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar13)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              *(float *)(iVar11 + 8 + uVar13 * 0x38) = local_2c;
              FUN_004052a0(local_2f4,&local_2c,4,local_28);
              FUN_00404788();
              iVar11 = *(int *)(*local_c + 0x1c);
              if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar13)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              *(float *)(iVar11 + 0xc + uVar13 * 0x38) = local_2c;
              FUN_004052a0(local_2f4,&local_2c,4,local_28);
              FUN_00404788();
              iVar11 = *(int *)(*local_c + 0x1c);
              if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar13)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              *(float *)(iVar11 + 0x10 + uVar13 * 0x38) = local_2c;
              FUN_004052a0(local_2f4,&local_2c,4,local_28);
              FUN_00404788();
              iVar11 = *(int *)(*local_c + 0x1c);
              if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar13)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              *(float *)(iVar11 + 0x14 + uVar13 * 0x38) = local_2c;
              FUN_004052a0(local_2f4,&local_2c,4,local_28);
              FUN_00404788();
              iVar11 = *(int *)(*local_c + 0x1c);
              if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar13)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              *(float *)(iVar11 + 0x18 + uVar13 * 0x38) = local_2c;
              FUN_004052a0(local_2f4,&local_2c,4,local_28);
              FUN_00404788();
              iVar11 = *(int *)(*local_c + 0x1c);
              if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar13)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              *(float *)(iVar11 + 0x20 + uVar13 * 0x38) = local_2c;
              FUN_004052a0(local_2f4,&local_2c,4,local_28);
              FUN_00404788();
              iVar11 = *(int *)(*local_c + 0x1c);
              if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar13)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              *(float *)(iVar11 + 0x24 + uVar13 * 0x38) = local_2c;
              FUN_004052a0(local_2f4,&local_2c,4,local_28);
              FUN_00404788();
              iVar11 = *(int *)(*local_c + 0x1c);
              if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar13)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              *(float *)(iVar11 + 0x28 + uVar13 * 0x38) = local_2c;
              FUN_004052a0(local_2f4,&local_2c,4,local_28);
              FUN_00404788();
              iVar11 = *(int *)(*local_c + 0x1c);
              if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar13)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              *(float *)(iVar11 + 0x30 + uVar13 * 0x38) = local_2c;
              iVar11 = *(int *)(*local_c + 0x1c);
              if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar13)) {
                    /* WARNING: Subroutine does not return */
                thunk_FUN_00404770();
              }
              FUN_0040877c(iVar11 + 0x34 + uVar13 * 0x38);
              FUN_004052a0(local_2f4,&local_21,1,local_28);
              FUN_00404788();
              for (uVar8 = (uint)local_21; uVar8 != 0; uVar8 = uVar8 - 1) {
                FUN_004052a0(local_2f4,&local_2f,1,local_28);
                FUN_00404788();
                FUN_00408eb8(&local_350,local_2f,0);
                iVar11 = *(int *)(*local_c + 0x1c);
                if ((iVar11 == 0) || (*(uint *)(iVar11 + -4) <= uVar13)) {
                    /* WARNING: Subroutine does not return */
                  thunk_FUN_00404770();
                }
                FUN_00408fac(iVar11 + 0x34 + uVar13 * 0x38,local_350);
              }
              uVar13 = uVar13 + 1;
              local_70 = local_70 - 1;
            } while (local_70 != 0);
// END original lines 744..911

// BEGIN original lines 1000..1034
            uVar13 = uVar13 + 1;
            local_70 = local_70 - 1;
          } while (local_70 != 0);
        }
      }
      else if (local_19 == 0x79) {
        local_14 = 0;
        do {
          local_18 = 0;
          do {
            FUN_004052a0(local_2f4,&local_2c,4,local_28);
            FUN_00404788();
            if (3 < local_14) {
                    /* WARNING: Subroutine does not return */
              thunk_FUN_00404770();
            }
            iVar11 = (int)((longlong)(int)local_14 * 2);
            if ((longlong)iVar11 != (longlong)(int)local_14 * 2) {
                    /* WARNING: Subroutine does not return */
              thunk_FUN_00404770();
            }
            if (3 < local_18) {
                    /* WARNING: Subroutine does not return */
              thunk_FUN_00404770();
            }
            *(float *)(*local_c + iVar11 * 8 + 0x20 + local_18 * 4) = local_2c;
            local_18 = local_18 + 1;
          } while (local_18 != 4);
          local_14 = local_14 + 1;
        } while (local_14 != 4);
        local_18 = 4;
        local_14 = 4;
      }
    }
    FUN_004052e0(local_2f4);
// END original lines 1000..1034
