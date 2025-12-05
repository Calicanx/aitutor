import * as React from "react"
import * as SliderPrimitive from "@radix-ui/react-slider"

import { cn } from "@/lib/utils"

const Slider = React.forwardRef<
  React.ElementRef<typeof SliderPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root>
>(({ className, ...props }, ref) => (
  <SliderPrimitive.Root
    ref={ref}
    className={cn(
      "relative flex w-full touch-none select-none items-center",
      className
    )}
    {...props}
  >
    <SliderPrimitive.Track className="relative h-3 w-full grow overflow-hidden rounded-none border-2 border-black dark:border-white bg-muted">
      <SliderPrimitive.Range className="absolute h-full bg-[#FFD93D]" />
    </SliderPrimitive.Track>
    <SliderPrimitive.Thumb className="block h-5 w-5 rounded-none border-[3px] border-black dark:border-white bg-[#FFFDF5] dark:bg-[#1a1a2e] shadow-[2px_2px_0_0_#000] dark:shadow-[2px_2px_0_0_#fff] transition-colors focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 hover:bg-[#FFD93D]" />
  </SliderPrimitive.Root>
))
Slider.displayName = SliderPrimitive.Root.displayName

export { Slider }
