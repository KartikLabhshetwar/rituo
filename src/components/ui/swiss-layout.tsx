"use client"

import { cn } from "@/lib/utils"
import { ReactNode } from "react"

interface SwissContainerProps {
  children: ReactNode
  className?: string
  maxWidth?: "sm" | "md" | "lg" | "xl" | "2xl" | "full"
}

export function SwissContainer({ children, className, maxWidth = "lg" }: SwissContainerProps) {
  const maxWidthClasses = {
    sm: "max-w-sm",
    md: "max-w-md", 
    lg: "max-w-4xl",
    xl: "max-w-6xl",
    "2xl": "max-w-7xl",
    full: "max-w-full"
  }

  return (
    <div className={cn("mx-auto px-4 sm:px-6 lg:px-8", maxWidthClasses[maxWidth], className)}>
      {children}
    </div>
  )
}

interface SwissGridProps {
  children: ReactNode
  columns?: 1 | 2 | 3 | 4
  gap?: "sm" | "md" | "lg"
  className?: string
}

export function SwissGrid({ children, columns = 2, gap = "md", className }: SwissGridProps) {
  const gridClasses = {
    1: "grid-cols-1",
    2: "grid-cols-1 md:grid-cols-2",
    3: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3", 
    4: "grid-cols-1 md:grid-cols-2 lg:grid-cols-4"
  }

  const gapClasses = {
    sm: "gap-4",
    md: "gap-6",
    lg: "gap-8"
  }

  return (
    <div className={cn("grid", gridClasses[columns], gapClasses[gap], className)}>
      {children}
    </div>
  )
}

interface SwissCardProps {
  children: ReactNode
  className?: string
  variant?: "default" | "outlined" | "elevated"
}

export function SwissCard({ children, className, variant = "default" }: SwissCardProps) {
  const variantClasses = {
    default: "bg-background",
    outlined: "bg-background border border-border",
    elevated: "bg-background border border-border shadow-sm"
  }

  return (
    <div className={cn("rounded-sm p-6", variantClasses[variant], className)}>
      {children}
    </div>
  )
}

interface SwissSectionProps {
  children: ReactNode
  className?: string
  background?: "default" | "muted"
}

export function SwissSection({ children, className, background = "default" }: SwissSectionProps) {
  const backgroundClasses = {
    default: "bg-background",
    muted: "bg-muted/30"
  }

  return (
    <section className={cn("py-12 sm:py-16 lg:py-20", backgroundClasses[background], className)}>
      {children}
    </section>
  )
}

interface SwissHeadingProps {
  children: ReactNode
  level?: 1 | 2 | 3 | 4 | 5 | 6
  className?: string
  align?: "left" | "center" | "right"
}

export function SwissHeading({ children, level = 1, className, align = "left" }: SwissHeadingProps) {
  const alignClasses = {
    left: "text-left",
    center: "text-center", 
    right: "text-right"
  }

  const baseClasses = "font-semibold tracking-tight text-foreground"
  
  const levelClasses = {
    1: "text-4xl sm:text-5xl lg:text-6xl",
    2: "text-3xl sm:text-4xl lg:text-5xl",
    3: "text-2xl sm:text-3xl lg:text-4xl",
    4: "text-xl sm:text-2xl lg:text-3xl",
    5: "text-lg sm:text-xl lg:text-2xl",
    6: "text-base sm:text-lg lg:text-xl"
  }

  const Component = `h${level}` as keyof React.JSX.IntrinsicElements

  return (
    <Component className={cn(baseClasses, levelClasses[level], alignClasses[align], className)}>
      {children}
    </Component>
  )
}

interface SwissTextProps {
  children: ReactNode
  size?: "sm" | "base" | "lg" | "xl"
  weight?: "normal" | "medium" | "semibold"
  color?: "default" | "muted" | "accent"
  className?: string
}

export function SwissText({ 
  children, 
  size = "base", 
  weight = "normal", 
  color = "default", 
  className 
}: SwissTextProps) {
  const sizeClasses = {
    sm: "text-sm",
    base: "text-base",
    lg: "text-lg", 
    xl: "text-xl"
  }

  const weightClasses = {
    normal: "font-normal",
    medium: "font-medium",
    semibold: "font-semibold"
  }

  const colorClasses = {
    default: "text-foreground",
    muted: "text-muted-foreground",
    accent: "text-primary"
  }

  return (
    <p className={cn(
      "leading-relaxed",
      sizeClasses[size], 
      weightClasses[weight], 
      colorClasses[color], 
      className
    )}>
      {children}
    </p>
  )
}
