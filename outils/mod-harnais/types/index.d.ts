// Le dernier passage de pytest vu par le mod, ou null s'il n'en a vu aucun
export type Tests = {
  // true si pytest a terminé sans erreur (code de sortie 0)
  isVert: boolean
  // Le résumé lu dans la sortie, par exemple "1 failed, 41 passed"
  resume: string
}

declare module 'claude-code' {
  interface PluginState {
    harnais: {
      tests: Tests | null
      isSoupapeActive: boolean
      appels: number
    }
  }
}
