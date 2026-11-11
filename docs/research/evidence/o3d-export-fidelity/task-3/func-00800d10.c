// 00800d10 FUN_00800d10 SHA256 c7765877620816dd4de4cceb21dce1996c8789c89ee550c1fb58440ee689a33e

void FUN_00800d10(undefined4 param_1,uint param_2,int param_3,int param_4)

{
  int iVar1;
  
  if (0x1f < param_3 - 1U) {
                    /* WARNING: Subroutine does not return */
    thunk_FUN_00404770();
  }
  if (7 < param_2) {
                    /* WARNING: Subroutine does not return */
    thunk_FUN_00404770();
  }
  iVar1 = (int)((longlong)(int)param_2 * 0x10);
  if ((longlong)iVar1 != (longlong)(int)param_2 * 0x10) {
                    /* WARNING: Subroutine does not return */
    thunk_FUN_00404770();
  }
  if (param_4 != (&DAT_00861ca8)[iVar1 * 2 + param_3]) {
    if (7 < param_2) {
                    /* WARNING: Subroutine does not return */
      thunk_FUN_00404770();
    }
    iVar1 = (int)((longlong)(int)param_2 * 0x10);
    if ((longlong)iVar1 != (longlong)(int)param_2 * 0x10) {
                    /* WARNING: Subroutine does not return */
      thunk_FUN_00404770();
    }
    (&DAT_00861ca8)[iVar1 * 2 + param_3] = param_4;
    (**(code **)(**(int **)PTR_DAT_00858824 + 0x10c))();
  }
  return;
}


