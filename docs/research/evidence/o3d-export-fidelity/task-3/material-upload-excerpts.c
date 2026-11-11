// Bounded evidence excerpt; not compilable source. Original: .superpowers/sdd/2026-11-10-o3d-export-fidelity/native-authorized-consumers/func-007fd9b0.c
// Original SHA256 240284972d1720cdd35f6bef7be4bad90fb557179e4a94ccee844e3af9577982; original bytes 91843
// Source line ranges (inclusive): [(1, 5), (150, 230), (2350, 2404)]

// BEGIN original lines 1..5
// 007fd9b0 FUN_007fd9b0 SHA256 c7765877620816dd4de4cceb21dce1996c8789c89ee550c1fb58440ee689a33e

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_007fd9b0(int param_1,uint *param_2,undefined4 param_3,int *param_4)
// END original lines 1..5

// BEGIN original lines 150..230
  int *local_30;
  int *piStack_2c;
  int *piStack_28;
  int *local_24;
  
  bVar14 = 0;
  iVar7 = 0x4d;
  do {
    iVar7 = iVar7 + -1;
  } while (iVar7 != 0);
  LOCK();
  UNLOCK();
  local_24 = (int *)0x0;
  puVar12 = &local_108;
  for (iVar7 = 0x2f; iVar7 != 0; iVar7 = iVar7 + -1) {
    *puVar12 = *param_2;
    param_2 = param_2 + 1;
    puVar12 = puVar12 + 1;
  }
  local_4c = local_24;
  local_24 = (int *)0x7fd9f2;
  local_10c = param_1;
  FUN_00409f30(&local_108,&DAT_007fa590);
  local_24 = (int *)0x7fd9fa;
  FUN_0040c0c4(local_4c);
  piStack_28 = (int *)&LAB_008005eb;
  piStack_2c = (int *)*in_FS_OFFSET;
  *in_FS_OFFSET = &piStack_2c;
  local_30 = (int *)0x7fda12;
  local_24 = (int *)&stack0xfffffffc;
  cVar5 = FUN_00805c78(0x40);
  if (cVar5 == '\0') goto LAB_0080046a;
  if (*PTR_DAT_00859e08 == '\0') {
    if ((local_ff == '\0') || (local_4c == (int *)0x0)) {
      local_30 = (int *)local_9c;
      piStack_34 = *(int **)PTR_DAT_00858824;
      piStack_38 = (int *)0x7fe2d4;
      (**(code **)(*piStack_34 + 0xc4))();
    }
    else {
      local_30 = (int *)(local_10c + 0x4c);
      piStack_34 = *(int **)PTR_DAT_00858824;
      piStack_38 = (int *)0x7fe2bb;
      (**(code **)(*piStack_34 + 0xc4))();
    }
    if (local_ab == '\0') {
      local_30 = (int *)0x7fe304;
      FUN_00800d80(DAT_00861ca8,0xe,1);
    }
    else {
      local_30 = (int *)0x7fe2ee;
      FUN_00800d80(DAT_00861ca8,0xe,0);
    }
    local_48 = (int *)0x0;
    local_30 = (int *)0x0;
    piStack_34 = (int *)0x7fe31c;
    FUN_00800d10(DAT_00861ca8,0,0x18);
    local_30 = (int *)0x0;
    piStack_34 = (int *)0x7fe332;
    FUN_00800d10(DAT_00861ca8,1,0x18);
    local_30 = (int *)0x0;
    piStack_34 = (int *)0x7fe348;
    FUN_00800d10(DAT_00861ca8,2,0x18);
    local_30 = (int *)0x0;
    piStack_34 = (int *)0x7fe35e;
    FUN_00800d10(DAT_00861ca8,3,0x18);
    local_30 = (int *)0x0;
    piStack_34 = (int *)0x7fe374;
    FUN_00800d10(DAT_00861ca8,4,0x18);
    local_30 = (int *)0x0;
    piStack_34 = (int *)0x7fe38a;
    FUN_00800d10(DAT_00861ca8,5,0x18);
    local_30 = (int *)0x0;
    piStack_34 = (int *)0x7fe3a0;
    FUN_00800d10(DAT_00861ca8,6,0x18);
    local_30 = (int *)0x0;
    piStack_34 = (int *)0x7fe3b6;
    FUN_00800d10(DAT_00861ca8,7,0x18);
    piStack_34 = (int *)&LAB_007fe46c;
    piStack_38 = (int *)*in_FS_OFFSET;
    *in_FS_OFFSET = &piStack_38;
// END original lines 150..230

// BEGIN original lines 2350..2404
         (local_44 = (undefined4 *)CONCAT22(local_44._2_2_,(undefined2)local_44),
         *PTR_DAT_0085891c != '\0')) &&
        (local_44 = (undefined4 *)CONCAT22(local_44._2_2_,(undefined2)local_44), DAT_00861bdc != 0))
       && (local_44 = (undefined4 *)CONCAT22(local_44._2_2_,(undefined2)local_44),
          *(int *)PTR_DAT_00859d94 != 0)) {
      local_30 = (int *)0x4;
      piStack_2c = param_4;
      piStack_38 = (int *)0x7fe28d;
      FUN_007fc500(local_10c,&local_108,DAT_00861be4);
    }
  }
  piStack_34 = (int *)&LAB_0080016c;
  piStack_38 = (int *)*in_FS_OFFSET;
  *in_FS_OFFSET = &piStack_38;
  if (local_ac == '\x01') {
    piStack_3c = (int *)0x800058;
    local_30 = (int *)&stack0xfffffffc;
    FUN_00800d80(DAT_00861ca8,0xab,1);
    piStack_3c = (int *)0x80006c;
    FUN_00800d80(DAT_00861ca8,0xf,1);
    piStack_3c = (int *)0x800080;
    FUN_00800d80(DAT_00861ca8,0x18,0x80);
    piStack_3c = (int *)0x800094;
    FUN_00800d80(DAT_00861ca8,0x19,5);
  }
  else if (local_ac == '\x02') {
    piStack_3c = (int *)0x8000b5;
    local_30 = (int *)&stack0xfffffffc;
    FUN_00800d80(DAT_00861ca8,0xab,1);
    piStack_3c = (int *)0x8000c6;
    FUN_00800d80(DAT_00861ca8,0xf,0);
    piStack_3c = (int *)0x8000da;
    FUN_00800d80(DAT_00861ca8,0x18,8);
    piStack_3c = (int *)0x8000ee;
    FUN_00800d80(DAT_00861ca8,0x19,5);
    piStack_3c = (int *)0x800102;
    FUN_00800d80(DAT_00861ca8,0x13,5);
    piStack_3c = (int *)0x800116;
    FUN_00800d80(DAT_00861ca8,0x14,6);
    piStack_3c = (int *)0x80012a;
    FUN_00800d80(DAT_00861ca8,0x1b,1);
  }
  else {
    piStack_3c = (int *)0x800140;
    local_30 = (int *)&stack0xfffffffc;
    FUN_00800d80(DAT_00861ca8,0xab,1);
    piStack_3c = (int *)0x800151;
    FUN_00800d80(DAT_00861ca8,0x1b,0);
    piStack_3c = (int *)0x800162;
    FUN_00800d80(DAT_00861ca8,0xf,0);
  }
  *in_FS_OFFSET = piStack_38;
  piStack_34 = (int *)&LAB_008001f0;
  piStack_38 = (int *)*in_FS_OFFSET;
  *in_FS_OFFSET = &piStack_38;
// END original lines 2350..2404
