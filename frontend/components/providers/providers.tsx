import type { ReactNode } from "react"

import { Toaster } from "@/components/ui/sonner"
import { TooltipProvider } from "@/components/ui/tooltip"

export function Providers({ children }: { children: ReactNode }) {
  return (
    <TooltipProvider>
      {children}
      {/* No celular, acima da barra inferior da área logada. */}
      <Toaster
        position="bottom-center"
        mobileOffset={{ bottom: "calc(5.5rem + env(safe-area-inset-bottom))" }}
      />
    </TooltipProvider>
  )
}
