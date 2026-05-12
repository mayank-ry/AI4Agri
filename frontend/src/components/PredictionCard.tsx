// frontend/src/components/PredictionCard.tsx
import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";

interface PredictionCardProps {
  result: {
    disease_name: string;
    disease_name_hi: string;
    confidence: number; // 0‑1
    severity: string;
    treatment_hi: string;
    /** Legacy / optional display field */
    model_used?: string;
    /** API returns `model_source` from disease pipeline */
    model_source?: string;
  };
}

export const PredictionCard: React.FC<PredictionCardProps> = ({ result }) => {
  const confidencePct = Math.round(result.confidence * 100);

  const source = result.model_source || result.model_used || "";
  const sourceLabel =
    source.includes("cnn") || source === "cnn"
      ? "CNN"
      : source.includes("vit") || source === "vit"
        ? "ViT Backup"
        : source || "Model";

  return (
    <motion.div
      className="w-full max-w-xl mx-auto"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <Card className="border-t-4 border-emerald-500 shadow-lg animate-fade-in">
        <CardHeader className="flex flex-col gap-2">
          <div className="flex justify-between items-center">
            <CardTitle className="text-2xl font-bold text-gray-800">
              {result.disease_name_hi}
            </CardTitle>
            <Badge variant="secondary" className="text-sm">
              {sourceLabel}
            </Badge>
          </div>
          <p className="text-sm text-gray-500">English: {result.disease_name}</p>
        </CardHeader>
        <CardContent>
          {/* Severity badge */}
          <div className="flex justify-between items-center mb-4">
            {result.severity === "severe" ? (
              <Badge variant="destructive">Severe 🔴</Badge>
            ) : result.severity === "moderate" ? (
              <Badge variant="outline" className="bg-orange-100 text-orange-700">
                Moderate 🟠
              </Badge>
            ) : (
              <Badge variant="secondary">Mild 🟡</Badge>
            )}
            <div className="text-right">
              <p className="text-xs text-gray-500">Confidence</p>
              <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden mt-1">
                <div
                  className="h-full bg-emerald-500"
                  style={{ width: `${confidencePct}%` }}
                />
              </div>
            </div>
          </div>

          {/* Treatment */}
          <div className="bg-emerald-50 p-4 rounded-lg">
            <h3 className="font-bold text-emerald-800 mb-2">इलाज (Treatment)</h3>
            <p className="text-gray-700 leading-relaxed text-sm">
              {result.treatment_hi}
            </p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};
