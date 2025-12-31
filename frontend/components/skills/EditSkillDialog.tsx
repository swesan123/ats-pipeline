"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { skillsApi } from "@/lib/api";

const skillSchema = z.object({
  name: z.string().min(1, "Skill name is required"),
  category: z.string().min(1, "Category is required"),
  proficiency: z.enum(["beginner", "intermediate", "advanced", "expert"]).optional(),
  keywords: z.array(z.string()).optional(),
  evidence: z.array(
    z.object({
      type: z.string(),
      description: z.string().optional(),
      link: z.string().optional(),
      start_date: z.string().optional(),
      end_date: z.string().optional(),
    })
  ).optional(),
});

type SkillFormValues = z.infer<typeof skillSchema>;

interface EditSkillDialogProps {
  skill: any;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function EditSkillDialog({
  skill,
  open,
  onOpenChange,
  onSuccess,
}: EditSkillDialogProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<SkillFormValues>({
    resolver: zodResolver(skillSchema),
    defaultValues: {
      name: skill?.name || "",
      category: skill?.category || "",
      proficiency: skill?.proficiency || "intermediate",
      keywords: skill?.keywords || [],
      evidence: skill?.evidence || [],
    },
  });

  useEffect(() => {
    if (open && skill) {
      form.reset({
        name: skill.name || "",
        category: skill.category || "",
        proficiency: skill.proficiency || "intermediate",
        keywords: skill.keywords || [],
        evidence: skill.evidence || [],
      });
    }
  }, [open, skill, form]);

  const handleSubmit = async (data: SkillFormValues) => {
    setLoading(true);
    setError(null);

    try {
      // Get all skills, update the one being edited, then save all
      const allSkills = await skillsApi.getUserSkills();
      const updatedSkills = allSkills.skills.map((s: any) =>
        s.name.toLowerCase() === skill.name.toLowerCase()
          ? {
              ...s,
              ...data,
            }
          : s
      );

      await skillsApi.updateUserSkills({ skills: updatedSkills });
      onSuccess?.();
      onOpenChange(false);
    } catch (err: any) {
      setError(err.message || "Failed to update skill");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Skill</DialogTitle>
          <DialogDescription>
            Update the skill information below.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Skill Name</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g., Python" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="category"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Category</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a category" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="Programming Languages">
                        Programming Languages
                      </SelectItem>
                      <SelectItem value="Frameworks & Libraries">
                        Frameworks & Libraries
                      </SelectItem>
                      <SelectItem value="Tools & Technologies">
                        Tools & Technologies
                      </SelectItem>
                      <SelectItem value="Databases">Databases</SelectItem>
                      <SelectItem value="Cloud & DevOps">
                        Cloud & DevOps
                      </SelectItem>
                      <SelectItem value="Other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="proficiency"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Proficiency Level</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select proficiency level" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="beginner">Beginner</SelectItem>
                      <SelectItem value="intermediate">Intermediate</SelectItem>
                      <SelectItem value="advanced">Advanced</SelectItem>
                      <SelectItem value="expert">Expert</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {error && (
              <div className="text-sm text-red-500 bg-red-50 p-3 rounded">
                {error}
              </div>
            )}

            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Update Skill
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
