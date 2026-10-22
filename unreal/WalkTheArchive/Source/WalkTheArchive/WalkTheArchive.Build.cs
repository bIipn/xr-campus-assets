// Walk the Archive - runtime module rules.
// Dependencies are the contract list (CONTRACT.md section 4). Nothing else in phase 0.

using UnrealBuildTool;

public class WalkTheArchive : ModuleRules
{
	public WalkTheArchive(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"UMG",
			"Slate",
			"SlateCore",
			"AIModule",
			"NavigationSystem",
			"DeveloperSettings"
		});

		PrivateDependencyModuleNames.AddRange(new string[] { "AnimationCore" });
	}
}
