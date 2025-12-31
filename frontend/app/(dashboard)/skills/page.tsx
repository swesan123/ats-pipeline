"use client";

import { useEffect, useState } from "react";
import { skillsApi, aiSkillSuggestionsApi } from "@/lib/api";
import { SkillsByCategory } from "@/components/skills/SkillsByCategory";
import { AddSkillDialog } from "@/components/skills/AddSkillDialog";
import { AISkillSuggestions } from "@/components/skills/AISkillSuggestions";
import {
  Alert,
  AlertDescription,
} from "@/components/ui/alert";

export default function SkillsPage() {
  const [skills, setSkills] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSkills();
  }, []);

  const loadSkills = async () => {
    try {
      setLoading(true);
      const data = await skillsApi.get();
      setSkills(data.skills || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load skills");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (skillName: string) => {
    if (!confirm(`Are you sure you want to delete "${skillName}"?`)) {
      return;
    }

    try {
      await skillsApi.delete(skillName);
      loadSkills();
    } catch (err: any) {
      setError(err.message || "Failed to delete skill");
    }
  };

  const handleAddSuggestedSkill = async (skillName: string, category?: string) => {
    try {
      // If category not provided, classify it using AI
      let skillCategory = category;
      if (!skillCategory) {
        try {
          const classification = await aiSkillSuggestionsApi.classifyCategory(skillName);
          skillCategory = classification.category;
        } catch (err) {
          // Fallback to Backend/DB if classification fails
          skillCategory = "Backend/DB";
        }
      }
      
      await skillsApi.add({
        name: skillName,
        category: skillCategory,
      });
      loadSkills();
    } catch (err: any) {
      setError(err.message || "Failed to add skill");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Skills</h1>
        <AddSkillDialog onSuccess={loadSkills} />
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>
            {error}
            <button
              onClick={loadSkills}
              className="ml-2 underline hover:no-underline"
            >
              Retry
            </button>
          </AlertDescription>
        </Alert>
      )}

      <AISkillSuggestions
        currentSkills={skills.map((s: any) => s.name)}
        onAddSkill={handleAddSuggestedSkill}
      />

      {loading && skills.length === 0 ? (
        <div className="text-center py-8 text-gray-500">Loading skills...</div>
      ) : (
        <SkillsByCategory
          skills={skills}
          onDelete={handleDelete}
          onUpdate={loadSkills}
        />
      )}
    </div>
  );
}
