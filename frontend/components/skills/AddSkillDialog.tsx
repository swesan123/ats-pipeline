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
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Loader2, Plus, X } from "lucide-react";
import { skillsApi, projectsApi, aiSkillSuggestionsApi } from "@/lib/api";

const evidenceSchema = z.object({
  source_type: z.string().min(1, "Evidence type is required"),
  source_name: z.string().min(1, "Evidence name is required"),
  evidence_text: z.string().optional(),
});

const skillSchema = z.object({
  name: z.string().min(1, "Skill name is required"),
  category: z.string().min(1, "Category is required"),
  evidence_sources: z.array(evidenceSchema).optional(),
});

type SkillFormValues = z.infer<typeof skillSchema>;
type EvidenceFormValues = z.infer<typeof evidenceSchema>;

interface AddSkillDialogProps {
  onSuccess?: () => void;
}

export function AddSkillDialog({ onSuccess }: AddSkillDialogProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableProjects, setAvailableProjects] = useState<string[]>([]);
  const [evidenceSources, setEvidenceSources] = useState<EvidenceFormValues[]>([]);

  const form = useForm<SkillFormValues>({
    resolver: zodResolver(skillSchema),
    defaultValues: {
      name: "",
      category: "",
      evidence_sources: [],
    },
  });

  useEffect(() => {
    if (open) {
      loadProjects();
    }
  }, [open]);

  const loadProjects = async () => {
    try {
      const projects = await projectsApi.list();
      setAvailableProjects(projects.map((p: any) => p.name));
    } catch (err) {
      // Silently fail - projects are optional
    }
  };

  const handleOpenChange = (newOpen: boolean) => {
    setOpen(newOpen);
    if (!newOpen) {
      form.reset();
      setError(null);
      setEvidenceSources([]);
    }
  };

  const addEvidenceSource = () => {
    setEvidenceSources([
      ...evidenceSources,
      { source_type: "", source_name: "", evidence_text: "" },
    ]);
  };

  const removeEvidenceSource = (index: number) => {
    const newSources = evidenceSources.filter((_, i) => i !== index);
    setEvidenceSources(newSources);
    form.setValue("evidence_sources", newSources);
  };

  const updateEvidenceSource = (
    index: number,
    field: keyof EvidenceFormValues,
    value: string
  ) => {
    const updated = [...evidenceSources];
    updated[index] = { ...updated[index], [field]: value };
    setEvidenceSources(updated);
    form.setValue("evidence_sources", updated);
  };

  const onSubmit = async (data: SkillFormValues) => {
    setLoading(true);
    setError(null);

    try {
      // Get existing skills
      const existingSkills = await skillsApi.get();
      const currentSkills = existingSkills.skills || [];

      // Filter out empty evidence sources
      const validEvidence = evidenceSources.filter(
        (ev) => ev.source_type && ev.source_name
      );

      // Add new skill - convert projects to evidence_sources
      const allEvidence = validEvidence.map((ev) => ({
        source_type: ev.source_type,
        source_name: ev.source_name,
        evidence_text: ev.evidence_text || undefined,
      }));
      
      const newSkill = {
        name: data.name,
        category: data.category,
        evidence_sources: allEvidence,
      };

      await skillsApi.update({
        skills: [...currentSkills, newSkill],
      });

      form.reset();
      setEvidenceSources([]);
      setOpen(false);
      onSuccess?.();
    } catch (err: any) {
      setError(err.message || "Failed to add skill");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button>Add Skill</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add New Skill</DialogTitle>
          <DialogDescription>
            Add a skill with category and associated projects.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Skill Name</FormLabel>
                  <FormControl>
                    <Input 
                      placeholder="Python, React, Docker" 
                      {...field}
                      onBlur={async (e) => {
                        field.onBlur();
                        // Auto-classify skill category if name is provided but category is empty
                        const skillName = e.target.value.trim();
                        const currentCategory = form.getValues("category");
                        if (skillName && !currentCategory) {
                          try {
                            const classification = await aiSkillSuggestionsApi.classifyCategory(skillName);
                            form.setValue("category", classification.category);
                          } catch (err) {
                            // Silently fail - user can manually select category
                          }
                        }
                      }}
                    />
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
                      <SelectItem value="Languages">Languages</SelectItem>
                      <SelectItem value="ML/AI">ML/AI</SelectItem>
                      <SelectItem value="Mobile/Web">Mobile/Web</SelectItem>
                      <SelectItem value="Backend/DB">Backend/DB</SelectItem>
                      <SelectItem value="DevOps">DevOps</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <FormLabel>Evidence Sources (Optional)</FormLabel>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addEvidenceSource}
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add Evidence
                </Button>
              </div>
              
              {/* Quick project selector */}
              {availableProjects.length > 0 && (
                <Select
                  value=""
                  onValueChange={(projectName) => {
                    if (projectName) {
                      const current = evidenceSources || [];
                      // Check if project already added
                      if (!current.some(ev => ev.source_type === 'project' && ev.source_name === projectName)) {
                        const newSources = [
                          ...current,
                          { source_type: 'project', source_name: projectName, evidence_text: '' }
                        ];
                        setEvidenceSources(newSources);
                        form.setValue("evidence_sources", newSources);
                      }
                    }
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Quick add project..." />
                  </SelectTrigger>
                  <SelectContent>
                    {availableProjects
                      .filter(project => 
                        !evidenceSources.some(ev => ev.source_type === 'project' && ev.source_name === project)
                      )
                      .map((project) => (
                        <SelectItem key={project} value={project}>
                          {project}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              )}
              {evidenceSources.map((evidence, index) => (
                <div
                  key={index}
                  className="p-3 border rounded-lg space-y-2"
                >
                  <div className="grid grid-cols-2 gap-2">
                    <Select
                      value={evidence.source_type}
                      onValueChange={(value) =>
                        updateEvidenceSource(index, "source_type", value)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Evidence type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="experience">Experience</SelectItem>
                        <SelectItem value="project">Project</SelectItem>
                        <SelectItem value="coursework">Coursework</SelectItem>
                        <SelectItem value="certification">
                          Certification
                        </SelectItem>
                      </SelectContent>
                    </Select>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Evidence name"
                        value={evidence.source_name}
                        onChange={(e) =>
                          updateEvidenceSource(
                            index,
                            "source_name",
                            e.target.value
                          )
                        }
                        className="flex-1"
                      />
                      {evidenceSources.length > 0 && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeEvidenceSource(index)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                  <Textarea
                    placeholder="Evidence snippet (optional)"
                    value={evidence.evidence_text || ""}
                    onChange={(e) =>
                      updateEvidenceSource(
                        index,
                        "evidence_text",
                        e.target.value
                      )
                    }
                    rows={2}
                  />
                </div>
              ))}
            </div>

            {error && (
              <div className="text-sm text-red-500 bg-red-50 p-3 rounded">
                {error}
              </div>
            )}

            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setOpen(false)}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Add Skill
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
