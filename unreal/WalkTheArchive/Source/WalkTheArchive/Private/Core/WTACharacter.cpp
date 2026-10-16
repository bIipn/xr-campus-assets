// Walk the Archive - the first-person player (port of the web nav.js player feel).

#include "Core/WTACharacter.h"
#include "Core/WTALog.h"
#include "Systems/WTAProgressSubsystem.h"
#include "AITypes.h"
#include "Blueprint/AIBlueprintHelperLibrary.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Controller.h"
#include "NavigationData.h"
#include "Navigation/PathFollowingComponent.h"

namespace
{
	/** The path-following component SimpleMoveToLocation attaches to the controller (null before the first walk). */
	UPathFollowingComponent* PathFollowingOf(const AController* Controller)
	{
		return Controller ? Controller->FindComponentByClass<UPathFollowingComponent>() : nullptr;
	}

	constexpr float CapsuleRadius = 30.f;
	constexpr float CapsuleHalfHeight = 90.f;
}

AWTACharacter::AWTACharacter()
{
	PrimaryActorTick.bCanEverTick = true;

	GetCapsuleComponent()->InitCapsuleSize(CapsuleRadius, CapsuleHalfHeight);

	// The camera sits at the eye: 162 cm above the floor = 72 cm above the capsule centre. Bob and dip move it.
	Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
	Camera->SetupAttachment(GetCapsuleComponent());
	Camera->SetRelativeLocation(FVector(0.f, 0.f, EyeHeight - CapsuleHalfHeight));
	Camera->bUsePawnControlRotation = true;
	Camera->SetFieldOfView(66.f);

	// The body turns with the camera yaw; pitch and roll stay on the camera only.
	bUseControllerRotationYaw = true;
	bUseControllerRotationPitch = false;
	bUseControllerRotationRoll = false;
	BaseEyeHeight = EyeHeight - CapsuleHalfHeight;

	// Web feel: walk 3 m/s, sprint 5.6, jump 5.2 m/s under 16 m/s^2, quick starts and stops, a little air control.
	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->MaxWalkSpeed = WalkSpeed;
	Move->JumpZVelocity = 520.f;
	Move->GravityScale = 1.63f;
	Move->MaxAcceleration = 3000.f;
	Move->BrakingDecelerationWalking = 4200.f;
	Move->BrakingFrictionFactor = 1.f;
	Move->AirControl = 0.25f;
	Move->bOrientRotationToMovement = false;
	Move->bUseControllerDesiredRotation = false;

	// No body mesh in phase 0: the player is a camera on a capsule.
	GetMesh()->SetVisibility(false);
	GetMesh()->SetOwnerNoSee(true);
}

void AWTACharacter::BeginPlay()
{
	Super::BeginPlay();
	GetCharacterMovement()->MaxWalkSpeed = bSprinting ? SprintSpeed : WalkSpeed;
	LastFrameLocation = GetActorLocation();
	bHasLastFrameLocation = true;
}

void AWTACharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// An auto-walk ends when the path follower stops moving (arrived, blocked or aborted).
	if (bAutoWalking)
	{
		const UPathFollowingComponent* Following = PathFollowingOf(GetController());
		if (Following == nullptr || Following->GetStatus() != EPathFollowingStatus::Moving)
		{
			bAutoWalking = false;
			GetCharacterMovement()->MaxWalkSpeed = bSprinting ? SprintSpeed : WalkSpeed;
		}
	}

	UpdateCameraOffset(DeltaSeconds);
	NoteDistanceWalked();
}

void AWTACharacter::Landed(const FHitResult& Hit)
{
	Super::Landed(Hit);
	// Landing dip: the faster the fall, the deeper the dip (web: dipV -= min(0.8 m/s, fall * 0.1)).
	const float FallSpeed = FMath::Max(0.f, static_cast<float>(-GetCharacterMovement()->Velocity.Z));
	DipVelocity -= FMath::Min(80.f, FallSpeed * LandingDipScale);
}

void AWTACharacter::WalkTo(FVector Dest)
{
	AController* OwnController = GetController();
	if (OwnController == nullptr)
	{
		return;
	}
	// Needs a NavMesh (the navmesh setup step). Without one the call logs a warning and nothing moves.
	UAIBlueprintHelperLibrary::SimpleMoveToLocation(OwnController, Dest);

	const UPathFollowingComponent* Following = PathFollowingOf(OwnController);
	if (Following != nullptr && Following->GetStatus() == EPathFollowingStatus::Moving)
	{
		float PathLength = static_cast<float>(FVector::Dist2D(GetActorLocation(), Dest));
		const FNavPathSharedPtr Path = Following->GetPath();
		if (Path.IsValid())
		{
			PathLength = static_cast<float>(Path->GetLength());
		}
		// Web: clamp(L / 2.3, 2.4, 12) m/s. Short hops stay slow, long trips move fast.
		GetCharacterMovement()->MaxWalkSpeed = FMath::Clamp(PathLength / 2.3f, TravelSpeedMin, TravelSpeedMax);
		bAutoWalking = true;
	}
	else
	{
		bAutoWalking = false;
		GetCharacterMovement()->MaxWalkSpeed = bSprinting ? SprintSpeed : WalkSpeed;
	}
}

void AWTACharacter::StopWalking()
{
	if (UPathFollowingComponent* Following = PathFollowingOf(GetController()))
	{
		if (Following->GetStatus() != EPathFollowingStatus::Idle)
		{
			Following->AbortMove(*this, FPathFollowingResultFlags::UserAbort);
		}
	}
	bAutoWalking = false;
	GetCharacterMovement()->MaxWalkSpeed = bSprinting ? SprintSpeed : WalkSpeed;
}

bool AWTACharacter::IsAutoWalking() const
{
	return bAutoWalking;
}

void AWTACharacter::TeleportToView(const FWTAView& View)
{
	if (!View.bValid)
	{
		return;
	}
	StopWalking();
	// View.Location is the eye; the capsule centre sits EyeHeight below it plus the half height.
	FVector Location = View.Location;
	Location.Z = View.Location.Z - EyeHeight + GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	SetActorLocation(Location, false, nullptr, ETeleportType::TeleportPhysics);
	GetCharacterMovement()->Velocity = FVector::ZeroVector;
	if (AController* OwnController = GetController())
	{
		OwnController->SetControlRotation(FRotator(View.Pitch, View.Yaw, 0.f));
	}
	SetActorRotation(FRotator(0.f, View.Yaw, 0.f));
	BobPhase = 0.f;
	BobAmount = 0.f;
	DipOffset = 0.f;
	DipVelocity = 0.f;
	LastFrameLocation = GetActorLocation();
	bHasLastFrameLocation = true;
}

FWTAView AWTACharacter::GetCurrentView() const
{
	FWTAView View;
	View.Location = GetEyeLocation();
	const FRotator Rotation = GetControlRotation().GetNormalized();
	View.Yaw = Rotation.Yaw;
	View.Pitch = Rotation.Pitch;
	View.bValid = true;
	return View;
}

FVector AWTACharacter::GetEyeLocation() const
{
	return Camera ? Camera->GetComponentLocation() : GetActorLocation() + FVector(0.f, 0.f, EyeHeight - CapsuleHalfHeight);
}

void AWTACharacter::SetSprinting(bool bOn)
{
	bSprinting = bOn;
	if (!bAutoWalking)
	{
		GetCharacterMovement()->MaxWalkSpeed = bSprinting ? SprintSpeed : WalkSpeed;
	}
}

void AWTACharacter::AddMoveInput(FVector2D Axis)
{
	if (Axis.IsNearlyZero())
	{
		return;
	}
	if (bAutoWalking)
	{
		StopWalking();
	}
	const FRotator YawRotation(0.f, GetControlRotation().Yaw, 0.f);
	const FVector Forward = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X);
	const FVector Right = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::Y);
	AddMovementInput(Forward, Axis.Y);
	AddMovementInput(Right, Axis.X);
}

void AWTACharacter::UpdateCameraOffset(float DeltaSeconds)
{
	if (Camera == nullptr || DeltaSeconds <= 0.f)
	{
		return;
	}
	const UCharacterMovementComponent* Move = GetCharacterMovement();
	const bool bOnGround = Move->IsMovingOnGround();
	const float Speed = static_cast<float>(GetVelocity().Size2D());

	// Head-bob: strength eases toward speed / walk speed while on the ground (web PLAYER.amp, k = 6).
	const float Want = (bOnGround && Speed > 40.f) ? FMath::Min(1.f, Speed / WalkSpeed) : 0.f;
	BobAmount = FMath::Lerp(BobAmount, Want, 1.f - FMath::Exp(-DeltaSeconds * 6.f));
	float Bob = 0.f;
	if (BobAmount > 0.002f)
	{
		BobPhase += DeltaSeconds * FMath::Max(Speed, 120.f) / BobStride;
		Bob = FMath::Sin(BobPhase * 2.f * PI) * BobAmplitude * BobAmount;
	}
	else
	{
		BobPhase = 0.f;
		BobAmount = 0.f;
	}

	// Landing dip: a damped spring (110, 15) back to zero.
	if (DipOffset != 0.f || DipVelocity != 0.f)
	{
		DipVelocity += (-110.f * DipOffset - 15.f * DipVelocity) * DeltaSeconds;
		DipOffset += DipVelocity * DeltaSeconds;
		if (FMath::Abs(DipOffset) < 0.04f && FMath::Abs(DipVelocity) < 0.4f)
		{
			DipOffset = 0.f;
			DipVelocity = 0.f;
		}
	}

	const float HalfHeight = GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	Camera->SetRelativeLocation(FVector(0.f, 0.f, EyeHeight - HalfHeight + Bob + DipOffset));
}

void AWTACharacter::NoteDistanceWalked()
{
	const FVector Location = GetActorLocation();
	if (bHasLastFrameLocation && GetCharacterMovement()->IsMovingOnGround())
	{
		const float Moved = static_cast<float>(FVector::Dist2D(Location, LastFrameLocation));
		// Teleports do not count as walking.
		if (Moved > 0.f && Moved < 300.f)
		{
			if (UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this))
			{
				Progress->NoteDistance(Moved);
			}
		}
	}
	LastFrameLocation = Location;
	bHasLastFrameLocation = true;
}
