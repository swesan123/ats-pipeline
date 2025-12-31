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

const experienceSchema = z.object({
  organization: z.string().min(1, "Organization is required"),
  role: z.string().min(1, "Role is required"),
  location: z.string().optional(),
  start_date: z.string().optional(),
  end_date: z.string().optional(),
});

type ExperienceFormValues = z.infer<typeof experienceSchema>;

interface ExperienceFormProps {
  initialValues?: {
    organization?: string;
    role?: string;
    location?: string;
    start_date?: string;
    end_date?: string;
    bullets?: Array<{ text: string }>;
  };
  onSubmit: (data: {
    organization: string;
    role: string;
    location?: string;
    start_date?: string;
    end_date?: string;
    bullets: Array<{ text: string; skills?: string[]; evidence?: string }>;
  }) => void;
  onCancel?: () => void;
  loading?: boolean;
}

export function ExperienceForm({
  initialValues,
  onSubmit,
  onCancel,
  loading,
}: ExperienceFormProps) {
  const [bullets, setBullets] = useState<string[]>(
    initialValues?.bullets?.map((b) => b.text) || [""]
  );
  const [roleDescription, setRoleDescription] = useState("");
  const [generatingBullets, setGeneratingBullets] = useState(false);
  const [formattingBullets, setFormattingBullets] = useState(false);
  const [bulletError, setBulletError] = useState<string | null>(null);

  const form = useForm<ExperienceFormValues>({
    resolver: zodResolver(experienceSchema),
    defaultValues: {
      organization: initialValues?.organization || "",
      role: initialValues?.role || "",
      location: initialValues?.location || "",
      start_date: initialValues?.start_date || "",
      end_date: initialValues?.end_date || "",
    },
  });

  const handleSubmit = (data: ExperienceFormValues) => {
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
      organization: data.organization,
      role: data.role,
      location: data.location || undefined,
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
    const role = form.getValues("role");
    const organization = form.getValues("organization");

    if (!role || !roleDescription.trim()) {
      setBulletError("Please provide a role and role description");
      return;
    }

    setGeneratingBullets(true);
    setBulletError(null);

    try {
      // Use role as project_name, roleDescription as description, organization as context
      const result = await aiBulletsApi.generate(
        `${role} at ${organization}`,
        roleDescription,
        [] // No tech stack for experience, but we can extract from bullets later
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
    const role = form.getValues("role");
    const organization = form.getValues("organization");

    const nonEmptyBullets = bullets.filter((b) => b.trim().length > 0);
    
    if (!role || nonEmptyBullets.length === 0) {
      setBulletError("Please provide a role and at least one bullet to format");
      return;
    }

    setFormattingBullets(true);
    setBulletError(null);

    try {
      const result = await aiBulletsApi.format(
        nonEmptyBullets,
        `${role} at ${organization}`,
        [] // No tech stack for experience
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
        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="organization"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Company/Organization</FormLabel>
                <FormControl>
                  <Input placeholder="Company Name" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="role"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Job Title/Role</FormLabel>
                <FormControl>
                  <Input placeholder="Software Engineer" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="location"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Location</FormLabel>
              <FormControl>
                <Input placeholder="Markham, ON" {...field} />
              </FormControl>
              <FormDescription>e.g., Markham, ON</FormDescription>
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
                <FormDescription>Format: YYYY-MM</FormDescription>
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
            <FormLabel>Role Description</FormLabel>
            <FormControl>
              <Textarea
                placeholder="Describe your responsibilities, key achievements, technologies used, and impact in this role..."
                value={roleDescription}
                onChange={(e) => setRoleDescription(e.target.value)}
                rows={4}
                className="resize-none"
              />
            </FormControl>
            <FormDescription>
              Provide a detailed description of your role and responsibilities. This will be used to generate professional resume bullets.
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
                disabled={generatingBullets || formattingBullets || !roleDescription.trim() || !form.getValues("role")}
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
                disabled={formattingBullets || generatingBullets || bullets.filter(b => b.trim().length > 0).length === 0 || !form.getValues("role")}
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
            Enter bullet points describing your accomplishments in this role. Use <strong>Format Bullets</strong> to ensure proper structure, bolding of technologies, and professional formatting. Use <strong>**Technology**</strong> to bold technologies (e.g., Built using <strong>**Python**</strong> and <strong>**TensorFlow**</strong>).
          </FormDescription>

          {bulletError && (
            <Alert variant="destructive">
              <AlertDescription>{bulletError}</AlertDescription>
            </Alert>
          )}

          {bullets.map((bullet, index) => (
            <div key={index} className="flex gap-2">
              <Textarea
                placeholder={`Bullet ${index + 1} - Start with an action verb (Built, Developed, Implemented...)`}
                value={bullet}
                onChange={(e) => updateBullet(index, e.target.value)}
                className="flex-1 font-mono text-sm"
                rows={2}
              />
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
            {loading ? "Saving..." : "Save Experience"}
          </Button>
        </div>
      </form>
    </Form>
  );
}
