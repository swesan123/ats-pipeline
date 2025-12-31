"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Plus, X, Sparkles, Loader2, Wand2 } from "lucide-react";
import { aiBulletsApi } from "@/lib/api";
import { Alert, AlertDescription } from "@/components/ui/alert";

const projectSchema = z.object({
  name: z.string().min(1, "Project name is required"),
  tech_stack: z.string().optional(),
  start_date: z.string().optional(),
  end_date: z.string().optional(),
});

type ProjectFormValues = z.infer<typeof projectSchema>;

interface ProjectFormProps {
  initialValues?: {
    name?: string;
    tech_stack?: string[];
    start_date?: string;
    end_date?: string;
    bullets?: Array<{ text: string }>;
  };
  onSubmit: (data: {
    name: string;
    tech_stack: string[];
    start_date?: string;
    end_date?: string;
    bullets: Array<{ text: string; skills?: string[]; evidence?: string }>;
  }) => void;
  onCancel?: () => void;
  loading?: boolean;
}

export function ProjectForm({
  initialValues,
  onSubmit,
  onCancel,
  loading,
}: ProjectFormProps) {
  const [bullets, setBullets] = useState<string[]>(
    initialValues?.bullets?.map((b) => b.text) || [""]
  );
  const [projectDescription, setProjectDescription] = useState("");
  const [generatingBullets, setGeneratingBullets] = useState(false);
  const [formattingBullets, setFormattingBullets] = useState(false);
  const [bulletError, setBulletError] = useState<string | null>(null);

  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      name: initialValues?.name || "",
      tech_stack: initialValues?.tech_stack?.join(", ") || "",
      start_date: initialValues?.start_date || "",
      end_date: initialValues?.end_date || "",
    },
  });

  const handleSubmit = (data: ProjectFormValues) => {
    const techStack = data.tech_stack
      ? data.tech_stack
          .split(",")
          .map((t) => t.trim())
          .filter((t) => t.length > 0)
      : [];

    // Convert YYYY-MM to "Jan 2024" format
    let startDate = data.start_date;
    if (startDate && startDate.match(/^\d{4}-\d{2}$/)) {
      const [year, month] = startDate.split("-");
      const date = new Date(parseInt(year), parseInt(month) - 1);
      startDate = date.toLocaleDateString("en-US", {
        month: "short",
        year: "numeric",
      });
    }

    let endDate = data.end_date;
    if (endDate && endDate.toLowerCase() !== "present" && endDate.match(/^\d{4}-\d{2}$/)) {
      const [year, month] = endDate.split("-");
      const date = new Date(parseInt(year), parseInt(month) - 1);
      endDate = date.toLocaleDateString("en-US", {
        month: "short",
        year: "numeric",
      });
    } else if (endDate && endDate.toLowerCase() === "present") {
      endDate = "Present";
    }

    const bulletsData = bullets
      .filter((b) => b.trim().length > 0)
      .map((text) => ({
        text: text.trim(),
        skills: [],
        evidence: undefined,
      }));

    onSubmit({
      name: data.name,
      tech_stack: techStack,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
      bullets: bulletsData,
    });
  };

  const addBullet = () => {
    setBullets([...bullets, ""]);
  };

  const removeBullet = (index: number) => {
    if (bullets.length > 1) {
      setBullets(bullets.filter((_, i) => i !== index));
    }
  };

  const updateBullet = (index: number, value: string) => {
    const newBullets = [...bullets];
    newBullets[index] = value;
    setBullets(newBullets);
  };

  const handleGenerateBullets = async () => {
    const projectName = form.getValues("name");
    const techStack = form.getValues("tech_stack")
      ? form.getValues("tech_stack")
          .split(",")
          .map((t) => t.trim())
          .filter((t) => t.length > 0)
      : [];

    if (!projectName || !projectDescription.trim()) {
      setBulletError("Please provide a project name and description");
      return;
    }

    setGeneratingBullets(true);
    setBulletError(null);

    try {
      const result = await aiBulletsApi.generate(
        projectName,
        projectDescription,
        techStack
      );
      
      if (result.bullets && result.bullets.length > 0) {
        setBullets(result.bullets);
      } else {
        setBulletError("No bullets generated. Please try again.");
      }
    } catch (err: any) {
      setBulletError(err.message || "Failed to generate bullets");
    } finally {
      setGeneratingBullets(false);
    }
  };

  const handleFormatBullets = async () => {
    const projectName = form.getValues("name");
    const techStack = form.getValues("tech_stack")
      ? form.getValues("tech_stack")
          .split(",")
          .map((t) => t.trim())
          .filter((t) => t.length > 0)
      : [];

    const nonEmptyBullets = bullets.filter((b) => b.trim().length > 0);
    
    if (!projectName || nonEmptyBullets.length === 0) {
      setBulletError("Please provide a project name and at least one bullet to format");
      return;
    }

    setFormattingBullets(true);
    setBulletError(null);

    try {
      const result = await aiBulletsApi.format(
        nonEmptyBullets,
        projectName,
        techStack
      );
      
      if (result.bullets && result.bullets.length > 0) {
        // Replace existing bullets with formatted ones, preserving empty slots
        const formattedBullets = [...result.bullets];
        // If we had empty bullets at the end, preserve them
        const emptyCount = bullets.length - nonEmptyBullets.length;
        for (let i = 0; i < emptyCount; i++) {
          formattedBullets.push("");
        }
        setBullets(formattedBullets);
      } else {
        setBulletError("No formatted bullets returned. Please try again.");
      }
    } catch (err: any) {
      setBulletError(err.message || "Failed to format bullets");
    } finally {
      setFormattingBullets(false);
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Project Name</FormLabel>
              <FormControl>
                <Input placeholder="My Awesome Project" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="tech_stack"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Tech Stack</FormLabel>
              <FormControl>
                <Input
                  placeholder="Python, React, Docker (comma-separated)"
                  {...field}
                />
              </FormControl>
              <FormDescription>
                Enter technologies separated by commas
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="start_date"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Start Date</FormLabel>
                <FormControl>
                  <Input type="month" placeholder="YYYY-MM" {...field} />
                </FormControl>
                <FormDescription>Format: YYYY-MM (e.g., 2024-01)</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="end_date"
            render={({ field }) => (
              <FormItem>
                <FormLabel>End Date</FormLabel>
                <FormControl>
                  <Input
                    type="month"
                    placeholder="YYYY-MM or Present"
                    {...field}
                  />
                </FormControl>
                <FormDescription>Format: YYYY-MM or Present</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="space-y-2">
          <FormItem>
            <FormLabel>Project Description</FormLabel>
            <FormControl>
              <Textarea
                placeholder="Describe what the project does, key features, technologies used, and your role..."
                value={projectDescription}
                onChange={(e) => setProjectDescription(e.target.value)}
                rows={4}
                className="resize-none"
              />
            </FormControl>
            <FormDescription>
              Provide a detailed description of the project. This will be used to generate professional resume bullets.
            </FormDescription>
          </FormItem>

          <div className="flex items-center justify-between">
            <FormLabel>Bullets</FormLabel>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleGenerateBullets}
                disabled={generatingBullets || formattingBullets || !projectDescription.trim() || !form.getValues("name")}
              >
                {generatingBullets ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-1" />
                    Generate Bullets
                  </>
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleFormatBullets}
                disabled={formattingBullets || generatingBullets || bullets.filter(b => b.trim().length > 0).length === 0 || !form.getValues("name")}
              >
                {formattingBullets ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                    Formatting...
                  </>
                ) : (
                  <>
                    <Wand2 className="h-4 w-4 mr-1" />
                    Format Bullets
                  </>
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addBullet}
                disabled={formattingBullets || generatingBullets}
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Bullet
              </Button>
            </div>
          </div>

          <FormDescription className="mt-1">
            Enter bullet points describing your project accomplishments. Use <strong>Format Bullets</strong> to ensure proper structure, bolding of technologies, and professional formatting. Use <strong>**Technology**</strong> to bold technologies (e.g., Built using <strong>**Python**</strong> and <strong>**TensorFlow**</strong>).
          </FormDescription>

          {bulletError && (
            <Alert variant="destructive">
              <AlertDescription>{bulletError}</AlertDescription>
            </Alert>
          )}
          {bullets.length === 0 && (
            <div className="text-sm text-gray-500 p-3 bg-gray-50 rounded-lg">
              <p className="font-medium mb-1">Bullet Format Guidelines:</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>Start with action verbs (Built, Developed, Implemented, Created, etc.)</li>
                <li>Use full sentences (not fragments)</li>
                <li>Include technologies in <strong>bold</strong> format: <strong>**Technology**</strong></li>
                <li>Focus on accomplishments, not just tasks</li>
                <li>Keep to 1-2 lines maximum</li>
              </ul>
              <p className="mt-2 text-xs">
                <strong>Tip:</strong> Fill in the project description above and click "Generate Bullets" to automatically create professional resume bullets. Or enter bullets manually and use "Format Bullets" to ensure proper structure and bolding.
              </p>
            </div>
          )}
          {bullets.map((bullet, index) => (
            <div key={index} className="flex gap-2">
              <div className="flex-1 space-y-1">
                <Textarea
                  placeholder={`Bullet ${index + 1} - Start with an action verb (Built, Developed, Implemented...)`}
                  value={bullet}
                  onChange={(e) => updateBullet(index, e.target.value)}
                  className="flex-1 font-mono text-sm"
                  rows={2}
                />
              </div>
              {bullets.length > 1 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeBullet(index)}
                  className="self-start"
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          ))}
        </div>

        <div className="flex justify-end gap-2">
          {onCancel && (
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
          )}
          <Button type="submit" disabled={loading}>
            {loading ? "Saving..." : "Save Project"}
          </Button>
        </div>
      </form>
    </Form>
  );
}
