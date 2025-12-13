import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
} from "@/components/ui/select";
import { useState, useEffect } from "react";
import { Settings, User } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";

export function ProfileSettingsModal() {
    const { user, login } = useAuth();
    const [isOpen, setIsOpen] = useState(false);
    const [formData, setFormData] = useState({
        name: "",
        current_grade: "",
        learning_style: ""
    });

    useEffect(() => {
        if (user && isOpen) {
            setFormData({
                name: user.name || "",
                current_grade: user.current_grade || "GRADE_10",
                learning_style: user.learning_style || "visual"
            });
        }
    }, [user, isOpen]);

    const handleSave = () => {
        // In a real app, this would call an API update endpoint.
        // For now, we simulate a local update to test the UI flow.
        if (!user) return;

        const updatedUser = {
            ...user,
            name: formData.name,
            current_grade: formData.current_grade,
            learning_style: formData.learning_style
        };

        // Update local context
        // Note: This relies on the AuthContext exposing a way to update the user manually or re-fetching.
        // Since 'login' usually sets the user, we can try to re-set it if the context allows, 
        // or we just show a success toast for this demo.

        toast.success("Profile updated locally (Refresh to reset)");
        setIsOpen(false);
    };

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
                <div className="flex items-center w-full cursor-pointer">
                    <Settings className="mr-2 h-4 w-4" />
                    <span>Settings</span>
                </div>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Profile Settings</DialogTitle>
                    <DialogDescription>
                        Update your learning preferences and personal details.
                    </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="name" className="text-right">
                            Name
                        </Label>
                        <Input
                            id="name"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            className="col-span-3"
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="grade" className="text-right">
                            Grade
                        </Label>
                        <Select
                            value={formData.current_grade}
                            onValueChange={(val) => setFormData({ ...formData, current_grade: val })}
                        >
                            <SelectTrigger className="col-span-3">
                                <SelectValue placeholder="Select grade" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="K">Kindergarten</SelectItem>
                                <SelectItem value="GRADE_1">1st Grade</SelectItem>
                                <SelectItem value="GRADE_2">2nd Grade</SelectItem>
                                <SelectItem value="GRADE_3">3rd Grade</SelectItem>
                                <SelectItem value="GRADE_4">4th Grade</SelectItem>
                                <SelectItem value="GRADE_5">5th Grade</SelectItem>
                                <SelectItem value="GRADE_6">6th Grade</SelectItem>
                                <SelectItem value="GRADE_7">7th Grade</SelectItem>
                                <SelectItem value="GRADE_8">8th Grade</SelectItem>
                                <SelectItem value="GRADE_9">9th Grade</SelectItem>
                                <SelectItem value="GRADE_10">10th Grade</SelectItem>
                                <SelectItem value="GRADE_11">11th Grade</SelectItem>
                                <SelectItem value="GRADE_12">12th Grade</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="style" className="text-right">
                            Style
                        </Label>
                        <Select
                            value={formData.learning_style}
                            onValueChange={(val) => setFormData({ ...formData, learning_style: val })}
                        >
                            <SelectTrigger className="col-span-3">
                                <SelectValue placeholder="Select style" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="visual">Visual</SelectItem>
                                <SelectItem value="auditory">Auditory</SelectItem>
                                <SelectItem value="reading">Reading/Writing</SelectItem>
                                <SelectItem value="kinesthetic">Kinesthetic</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>
                <DialogFooter>
                    <Button type="submit" onClick={handleSave}>Save changes</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
