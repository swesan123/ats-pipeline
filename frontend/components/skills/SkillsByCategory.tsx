"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Edit, Trash2 } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronDown } from "lucide-react";
import { EditSkillDialog } from "./EditSkillDialog";

interface Skill {
  name: string;
  category: string;
  proficiency?: string;
  keywords?: string[];
  evidence?: Array<{
    type: string;
    description?: string;
    link?: string;
    start_date?: string;
    end_date?: string;
  }>;
  projects?: string[];
  evidence_sources?: Array<{
    source_type: string;
    source_name: string;
    evidence_text?: string;
  }>;
}

interface SkillsByCategoryProps {
  skills: Skill[];
  onEdit?: (skill: Skill) => void;
  onDelete?: (skillName: string) => void;
  onUpdate?: () => void;
}

export function SkillsByCategory({
  skills,
  onEdit,
  onDelete,
  onUpdate,
}: SkillsByCategoryProps) {
  const [editingSkill, setEditingSkill] = useState<Skill | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  const handleEdit = (skill: Skill) => {
    setEditingSkill(skill);
    setEditDialogOpen(true);
    onEdit?.(skill);
  };

  const handleEditSuccess = () => {
    setEditDialogOpen(false);
    setEditingSkill(null);
    onUpdate?.();
  };
  const grouped = skills.reduce((acc, skill) => {
    const category = skill.category || "Other";
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(skill);
    return acc;
  }, {} as Record<string, Skill[]>);

  const categories = Object.keys(grouped).sort();

  if (categories.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No skills added yet. Add a skill to get started.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {categories.map((category) => (
        <Card key={category}>
          <Collapsible defaultOpen>
            <CollapsibleTrigger asChild>
              <CardHeader className="cursor-pointer hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">
                    {category} ({grouped[category].length})
                  </CardTitle>
                  <ChevronDown className="h-4 w-4" />
                </div>
              </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <CardContent>
                <div className="space-y-3">
                  {grouped[category].map((skill) => (
                    <div
                      key={skill.name}
                      className="flex items-start justify-between p-3 border rounded-lg"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-medium">{skill.name}</span>
                        </div>
                        {skill.projects && skill.projects.length > 0 && (
                          <div className="flex flex-wrap gap-1 mb-2">
                            {skill.projects.map((project) => (
                              <Badge key={project} variant="outline">
                                {project}
                              </Badge>
                            ))}
                          </div>
                        )}
                        {skill.evidence_sources &&
                          skill.evidence_sources.length > 0 && (
                            <div className="text-xs text-gray-600">
                              {skill.evidence_sources
                                .map((ev) => ev.source_name)
                                .join(", ")}
                            </div>
                          )}
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(skill)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        {onDelete && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onDelete(skill.name)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </CollapsibleContent>
          </Collapsible>
        </Card>
      ))}

      {editingSkill && (
        <EditSkillDialog
          skill={editingSkill}
          open={editDialogOpen}
          onOpenChange={setEditDialogOpen}
          onSuccess={handleEditSuccess}
        />
      )}
    </div>
  );
}
