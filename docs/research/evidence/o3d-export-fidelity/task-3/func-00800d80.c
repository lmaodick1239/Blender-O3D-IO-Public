// 00800d80 FUN_00800d80 SHA256 c7765877620816dd4de4cceb21dce1996c8789c89ee550c1fb58440ee689a33e

void FUN_00800d80(undefined4 param_1,int param_2,int param_3)

{
  if (0xca < param_2 - 7U) {
                    /* WARNING: Subroutine does not return */
    thunk_FUN_00404770();
  }
  if (param_3 != *(int *)(&DAT_00862090 + param_2 * 4)) {
    *(int *)(&DAT_00862090 + param_2 * 4) = param_3;
    (**(code **)(**(int **)PTR_DAT_00858824 + 0xe4))();
  }
  return;
}


