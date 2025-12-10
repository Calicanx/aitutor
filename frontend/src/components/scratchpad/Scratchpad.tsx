import React, { useState, useRef } from "react";
import { ReactSketchCanvas, ReactSketchCanvasRef } from "react-sketch-canvas";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

const Scratchpad = () => {
  const [strokeColor, setStrokeColor] = useState("#000000");
  const [strokeWidth, setStrokeWidth] = useState(4);
  const [isErasing, setErasing] = useState(false);
  const canvasRef = useRef<ReactSketchCanvasRef>(null);

  const toggleEraser = () => {
    setErasing((prev) => {
      const next = !prev;
      if (canvasRef.current) {
        canvasRef.current.eraseMode(next);
      }
      return next;
    });
  };

  const handleUndo = () => {
    canvasRef.current?.undo();
  };

  const handleRedo = () => {
    canvasRef.current?.redo();
  };

  const handleClearAll = () => {
    canvasRef.current?.clearCanvas();
  };

  return (
    <div className="relative h-full w-full">
      <div className="absolute right-3 top-3 z-20 flex flex-col gap-2 rounded-md border border-border bg-background/90 p-3 shadow-md backdrop-blur">
        <div className="flex items-center justify-between gap-2">
          <Label htmlFor="scratchpad-color" className="text-xs text-muted-foreground">
            Stroke
          </Label>
          <input
            id="scratchpad-color"
            type="color"
            value={strokeColor}
            onChange={(e) => setStrokeColor(e.target.value)}
            className="h-6 w-6 cursor-pointer rounded border border-input bg-transparent p-0"
          />
        </div>

        <div className="space-y-1">
          <div className="flex items-center justify-between text-[10px] text-muted-foreground">
            <span>Width</span>
            <span>{strokeWidth}px</span>
          </div>
          <Slider
            value={[strokeWidth]}
            min={1}
            max={20}
            step={1}
            onValueChange={([value]) => setStrokeWidth(value)}
            className="w-40"
          />
        </div>

        {/* Eraser and Undo/Redo Row */}
        <div className="mt-1 flex items-center justify-between gap-2">
          <Button
            type="button"
            size="icon"
            variant={isErasing ? "secondary" : "outline"}
            onClick={toggleEraser}
            className="h-8 w-8"
            title={isErasing ? "Switch to Draw" : "Switch to Eraser"}
          >
            <span className="material-symbols-outlined text-base">
              {isErasing ? "edit" : "ink_eraser"}
            </span>
          </Button>
          <Button
            type="button"
            size="icon"
            variant="outline"
            onClick={handleUndo}
            className="h-8 w-8"
            title="Undo (Ctrl+Z)"
          >
            <span className="material-symbols-outlined text-base">undo</span>
          </Button>
          <Button
            type="button"
            size="icon"
            variant="outline"
            onClick={handleRedo}
            className="h-8 w-8"
            title="Redo (Ctrl+Y)"
          >
            <span className="material-symbols-outlined text-base">redo</span>
          </Button>
        </div>

        {/* Clear All with Confirmation */}
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button
              type="button"
              size="sm"
              variant="destructive"
              className="w-full text-xs"
            >
              <span className="material-symbols-outlined mr-1 text-sm">delete_forever</span>
              Clear All
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Clear entire canvas?</AlertDialogTitle>
              <AlertDialogDescription>
                This will delete all your work on the scratchpad. This action cannot be undone.
                Are you sure you want to continue?
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={handleClearAll} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                Clear All
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* Instructions */}
        <div className="mt-2 border-t border-border pt-2 text-[10px] text-muted-foreground">
          <p className="mb-1">💡 Tips:</p>
          <ul className="space-y-0.5 pl-3">
            <li>• Use eraser to remove strokes</li>
            <li>• Undo removes last stroke</li>
            <li>• Clear All removes everything</li>
          </ul>
        </div>
      </div>

      <ReactSketchCanvas
        ref={canvasRef}
        className="h-full w-full rounded-md border border-border bg-card/60 shadow-sm"
        strokeWidth={strokeWidth}
        strokeColor={strokeColor}
        canvasColor="rgba(255, 255, 255, 0.5)"
      />
    </div>
  );
};

export default Scratchpad;
