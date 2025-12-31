"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Loader2, AlertCircle } from "lucide-react";
import { jobsApi } from "@/lib/api";
import { Alert, AlertDescription } from "@/components/ui/alert";

const jobSchema = z.object({
  url: z.string().optional(),
  description: z.string().optional(),
}).refine(
  (data) => {
    // At least one of url or description must be provided
    return !!(data.url?.trim() || data.description?.trim());
  },
  {
    message: "Please provide either a URL or description",
    path: ["url"], // Show error on url field
  }
);

type JobFormValues = z.infer<typeof jobSchema>;

interface AddJobDialogProps {
  onSuccess?: () => void;
}

export function AddJobDialog({ onSuccess }: AddJobDialogProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("url");

  const form = useForm<JobFormValues>({
    resolver: zodResolver(jobSchema),
    defaultValues: {
      url: "",
      description: "",
    },
  });

  const onSubmit = async (data: JobFormValues) => {
    setLoading(true);
    setError(null);

    try {
      if (activeTab === "url") {
        if (!data.url || data.url.trim() === "") {
          setError("Please enter a job URL");
          setLoading(false);
          return;
        }
        // Validate URL format
        try {
          new URL(data.url);
        } catch {
          setError("Please enter a valid URL (e.g., https://example.com/job)");
          setLoading(false);
          return;
        }
        await jobsApi.create({ url: data.url });
      } else if (activeTab === "description") {
        if (!data.description || data.description.trim() === "") {
          setError("Please enter a job description");
          setLoading(false);
          return;
        }
        await jobsApi.create({
          description: data.description,
        });
      } else {
        setError("Please provide either a URL or description");
        setLoading(false);
        return;
      }

      form.reset();
      setOpen(false);
      onSuccess?.();
    } catch (err: any) {
      const errorMsg = err?.message || err?.detail || String(err) || "Failed to create job";
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Add Job</Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Add New Job</DialogTitle>
          <DialogDescription>
            Add a job posting by URL or description text.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="url">From URL</TabsTrigger>
                <TabsTrigger value="description">From Description</TabsTrigger>
              </TabsList>

              <TabsContent value="url" className="space-y-4">
                <FormField
                  control={form.control}
                  name="url"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Job URL</FormLabel>
                      <FormControl>
                        <Input
                          type="url"
                          placeholder="https://example.com/job-posting"
                          {...field}
                          aria-describedby="url-description"
                        />
                      </FormControl>
                      <FormDescription id="url-description">
                        Enter the URL of the job posting to scrape. The system will automatically extract job details.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </TabsContent>

              <TabsContent value="description" className="space-y-4">
                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Job Description</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="Paste the job description here..."
                          className="min-h-[200px]"
                          {...field}
                          aria-describedby="description-help"
                        />
                      </FormControl>
                      <FormDescription id="description-help">
                        Paste the full job description text. Job title, company, and other details will be automatically extracted from the description.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </TabsContent>
            </Tabs>

            {error && (
              <Alert variant="destructive" role="alert">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  {typeof error === 'string' ? error : String(error)}
                </AlertDescription>
              </Alert>
            )}

            <DialogFooter>
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
                Add Job
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
