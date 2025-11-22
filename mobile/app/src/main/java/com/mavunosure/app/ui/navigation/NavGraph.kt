package com.mavunosure.app.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.mavunosure.app.ui.auth.AuthScreen
import com.mavunosure.app.ui.home.ClaimDetailScreen
import com.mavunosure.app.ui.home.HomeScreen

sealed class Screen(val route: String) {
    object Auth : Screen("auth")
    object Home : Screen("home")
    object ClaimDetail : Screen("claim/{claimId}") {
        fun createRoute(claimId: String) = "claim/$claimId"
    }
}

@Composable
fun NavGraph(
    navController: NavHostController,
    startDestination: String
) {
    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        composable(Screen.Auth.route) {
            AuthScreen(
                onAuthSuccess = {
                    navController.navigate(Screen.Home.route) {
                        popUpTo(Screen.Auth.route) { inclusive = true }
                    }
                }
            )
        }
        
        composable(Screen.Home.route) {
            HomeScreen(
                onNewVerificationClick = {
                    // TODO: Navigate to camera screen when implemented
                },
                onClaimClick = { claimId ->
                    navController.navigate(Screen.ClaimDetail.createRoute(claimId))
                }
            )
        }
        
        composable(
            route = Screen.ClaimDetail.route,
            arguments = listOf(
                navArgument("claimId") { type = NavType.StringType }
            )
        ) { backStackEntry ->
            val claimId = backStackEntry.arguments?.getString("claimId") ?: return@composable
            ClaimDetailScreen(
                claimId = claimId,
                onNavigateBack = { navController.popBackStack() }
            )
        }
    }
}
