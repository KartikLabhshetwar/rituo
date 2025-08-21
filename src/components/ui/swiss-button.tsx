"use client"

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const swissButtonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary: "bg-foreground text-background hover:bg-foreground/90",
        secondary: "bg-muted text-foreground hover:bg-muted/80 border border-border",
        outline: "border border-foreground text-foreground hover:bg-foreground hover:text-background",
        ghost: "text-foreground hover:bg-muted",
        link: "text-foreground underline-offset-4 hover:underline"
      },
      size: {
        sm: "h-8 px-3 text-sm rounded-sm",
        default: "h-10 px-4 text-sm rounded-sm",
        lg: "h-12 px-6 text-base rounded-sm",
        xl: "h-14 px-8 text-lg rounded-sm"
      }
    },
    defaultVariants: {
      variant: "primary",
      size: "default"
    }
  }
)

export interface SwissButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof swissButtonVariants> {
  asChild?: boolean
}

const SwissButton = React.forwardRef<HTMLButtonElement, SwissButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(swissButtonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
SwissButton.displayName = "SwissButton"

export { SwissButton, swissButtonVariants }
