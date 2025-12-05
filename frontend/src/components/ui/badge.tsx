import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-none border-2 border-black dark:border-white px-2.5 py-0.5 text-xs font-black uppercase tracking-wide transition-colors focus:outline-none",
  {
    variants: {
      variant: {
        default:
          "bg-[#FFD93D] text-black shadow-[2px_2px_0_0_#000] dark:shadow-[2px_2px_0_0_#fff]",
        secondary:
          "bg-[#C4B5FD] text-black shadow-[2px_2px_0_0_#000] dark:shadow-[2px_2px_0_0_#fff]",
        destructive:
          "bg-[#FF6B6B] text-white shadow-[2px_2px_0_0_#000] dark:shadow-[2px_2px_0_0_#fff]",
        outline: "bg-transparent text-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
