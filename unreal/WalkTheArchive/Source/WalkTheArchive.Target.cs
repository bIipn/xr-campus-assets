// Walk the Archive - game target.

using UnrealBuildTool;
using System.Collections.Generic;

public class WalkTheArchiveTarget : TargetRules
{
	public WalkTheArchiveTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("WalkTheArchive");
	}
}
